from django.shortcuts import redirect, render
from parkingapp.models import Upload_File, Contact_Message, Feedback, User_details
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import cv2
import pickle
import numpy as np
import io
from PIL import Image
import cvzone
from django.http import StreamingHttpResponse, HttpResponse
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Import detection configuration
from parkingapp.detection_config import PIXEL_COUNT_THRESHOLDS, get_pixel_threshold

# YOLOv8 Integration
# Only enable on production with sufficient memory (Starter tier+) or development
ENABLE_YOLOV8 = os.getenv('ENABLE_YOLOV8', 'False').lower() == 'true'
YOLOV8_AVAILABLE = False

if ENABLE_YOLOV8:
    try:
        from parkingapp.yolov8_detection import ParkingSpaceDetector
        YOLOV8_AVAILABLE = True
    except ImportError as e:
        print(f"[WARNING] YOLOv8 not available. Error: {e}")
        print("[INFO] Install with: pip install ultralytics")
        print("[INFO] Create parkingapp/yolov8_detection.py with ParkingSpaceDetector class")
    except ModuleNotFoundError:
        print("[WARNING] yolov8_detection module not found. Please create parkingapp/yolov8_detection.py")
    except Exception as e:
        print(f"[WARNING] YOLOv8 import error: {type(e).__name__}: {e}")
else:
    print("[INFO] YOLOv8 disabled (requires ENABLE_YOLOV8=true env variable)")

# Global YOLOv8 detector instance (initialized once for performance)
yolo_detector = None

def get_yolo_detector():
    """Initialize YOLOv8 detector on first use"""
    global yolo_detector
    if yolo_detector is None and YOLOV8_AVAILABLE:
        try:
            print("[INFO] Initializing YOLOv8 detector...")
            yolo_detector = ParkingSpaceDetector(model_name='yolov8n.pt')
            print("[SUCCESS] YOLOv8 detector ready! 95%+ accuracy enabled")
        except FileNotFoundError as e:
            print(f"[ERROR] Model file not found: {e}")
            print("[INFO] YOLOv8 will attempt to auto-download the model on next use")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to initialize YOLOv8: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    return yolo_detector

# Create your views here.

def HomePage(request):
    return render(request, 'Home.html')

def AboutPage(request):
    return render(request, 'about.html')

def ContactPage(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        # Validate all fields
        if not all([name, email, subject, message_text]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'contact.html')
        
        # Validate email format
        if '@' not in email or len(email) < 5:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'contact.html')
        
        # Validate field lengths
        if len(name) > 100 or len(name) < 2:
            messages.error(request, 'Name must be between 2 and 100 characters.')
            return render(request, 'contact.html')
        
        if len(subject) > 200:
            messages.error(request, 'Subject must be less than 200 characters.')
            return render(request, 'contact.html')
        
        if len(message_text) > 5000:
            messages.error(request, 'Message must be less than 5000 characters.')
            return render(request, 'contact.html')
        
        try:
            # Save to database
            Contact_Message.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message_text
            )
            messages.success(request, 'Thank you! Your message has been sent successfully.')
            return redirect('contact')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Contact form error: {str(e)}')
            messages.error(request, 'Error sending message. Please try again.')
            return render(request, 'contact.html')
    return render(request, 'contact.html')

def FeedbackPage(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        # Validate all fields
        if not all([username, email, message_text]):
            messages.error(request, 'Please fill in all fields.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # Validate email format
        if '@' not in email or len(email) < 5:
            messages.error(request, 'Please enter a valid email address.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # Validate field lengths
        if len(username) > 100 or len(username) < 2:
            messages.error(request, 'Username must be between 2 and 100 characters.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        if len(message_text) > 5000:
            messages.error(request, 'Message must be less than 5000 characters.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        try:
            # Save to database
            Feedback.objects.create(
                username=username,
                email=email,
                message=message_text
            )
            messages.success(request, 'Thank you for your feedback!')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Feedback form error: {str(e)}')
            messages.error(request, 'Error submitting feedback. Please try again.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

def LoginPage(request):
    """Regular user login page - for non-admin users only"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Input validation
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('login')
        
        if len(password) < 6:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')
        
        # Check User_details table (custom user model)
        try:
            user = User_details.objects.get(Email=email)
            
            # Try Django's password verification first (for properly hashed passwords)
            password_valid = False
            try:
                password_valid = check_password(password, user.Password)
            except:
                pass
            
            # If not valid with Django hasher, try direct comparison (for simple hashes)
            if not password_valid:
                import hashlib
                simple_hash = hashlib.md5(password.encode()).hexdigest()[:15]
                password_valid = (user.Password == simple_hash)
            
            if password_valid:
                messages.success(request, 'Login Successful!')
                request.session['user_email'] = user.Email
                request.session['user_id'] = user.User_id
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
                return redirect('login')
        except User_details.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Login error for {email}: {str(e)}')
            messages.error(request, 'Login error. Please try again.')
            return redirect('login')
    
    return render(request, 'loginpage.html')

def AdminLoginPage(request):
    """Dedicated admin login page - for admin users only - Accepts username or email"""
    if request.method == 'POST':
        username_or_email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        # Input validation
        if not username_or_email or not password:
            messages.error(request, 'Username/Email and password are required.')
            return render(request, 'admin_login.html')
        
        # Try Django authentication first with username
        try:
            user = authenticate(request, username=username_or_email, password=password)
            
            # If username auth fails, try email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None and (user.is_staff or user.is_superuser):
                login(request, user)
                messages.success(request, 'Admin Login Successful!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Access Denied! Admin credentials required.')
                return render(request, 'admin_login.html')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Admin login error for {username_or_email}: {str(e)}')
            messages.error(request, 'Login error. Please try again.')
            return render(request, 'admin_login.html')
    
    return render(request, 'admin_login.html')

def SignupPage(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validate inputs
        if not email or not password or not confirm_password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        # Strong password requirements
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'signup.html')
        
        if not any(c.isupper() for c in password):
            messages.error(request, 'Password must contain at least one uppercase letter.')
            return render(request, 'signup.html')
        
        if not any(c.isdigit() for c in password):
            messages.error(request, 'Password must contain at least one digit.')
            return render(request, 'signup.html')
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'signup.html')
        
        # Check if user already exists
        if User_details.objects.filter(Email=email).exists():
            messages.error(request, 'Email already registered. Please login or use a different email.')
            return render(request, 'signup.html')
        
        try:
            # Create new user with simple MD5 hash (compatible with existing database)
            import hashlib
            hashed_password = hashlib.md5(password.encode()).hexdigest()[:15]
            User_details.objects.create(
                Email=email,
                Password=hashed_password
            )
            messages.success(request, 'Account created successfully! Please login with your credentials.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')

def LogoutPage(request):
    """Logout user and clear session"""
    # Clear Django session
    from django.contrib.auth import logout as django_logout
    django_logout(request)
    
    # Clear custom session data
    if 'user_email' in request.session:
        del request.session['user_email']
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'is_admin' in request.session:
        del request.session['is_admin']
    if 'admin_user' in request.session:
        del request.session['admin_user']
    
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def DashboardPage(request):
    return render(request, 'dashboard.html')

def display_image(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img)
    buffer = io.BytesIO()
    pil_img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def detect_text(image):
    from easyocr import Reader
    reader = Reader(['en'])
    result = reader.readtext(image)
    return result

def draw_boxes(image, result):
    for (bbox, text, prob) in result:
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple([int(val) for val in top_left])
        bottom_right = tuple([int(val) for val in bottom_right])
        image = cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        image = cv2.putText(image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
    return image

def detect_numberplate(request):
    if request.method == 'POST':
        # Check if file is uploaded
        if 'upload_file' not in request.FILES or not request.FILES['upload_file']:
            messages.error(request, 'Please upload an image file to detect license plate.')
            return render(request, 'licenseplate.html')
        
        try:
            image = request.FILES['upload_file']
            
            # Validate file size (max 10MB)
            if image.size > 10 * 1024 * 1024:
                messages.error(request, 'File size exceeds 10MB limit. Please upload a smaller image.')
                return render(request, 'licenseplate.html')
            
            np_img = np.frombuffer(image.read(), np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            
            if img is None:
                messages.error(request, 'Unable to read image file. Please upload a valid image format (JPG, PNG, etc.)')
                return render(request, 'licenseplate.html')

            # Detect text in the image
            result = detect_text(img)

            # Draw bounding boxes around detected text
            img_with_boxes = draw_boxes(img, result)

            # Convert the processed image to a format suitable for HttpResponse
            buffer = display_image(img_with_boxes)
            messages.success(request, 'License plate detected successfully!')
            return HttpResponse(buffer, content_type='image/png')
        
        except Exception as e:
            messages.error(request, f'Error processing image: {str(e)}')
            return render(request, 'licenseplate.html')
    
    return render(request, 'licenseplate.html')

def generate_frames_yolov8(cap, posList, detection_type='multi_lane'):
    """
    Image Processing-based parking detection with corrected thresholds
    """
    width, height = 107, 48
    frame_count = 0

    # Hardcoded thresholds optimized for your parking lot
    detection_config = {
        'multi_lane': {'threshold': 600, 'name': 'Multi-Lane Detection'},
        'reserved_spot': {'threshold': 550, 'name': 'Reserved Spot Recognition'},
        'night_vision': {'threshold': 500, 'name': 'Night Vision Detection'},
        'angled_spot': {'threshold': 580, 'name': 'Angled Spot Tracking'},
    }
    
    config = detection_config.get(detection_type, detection_config['multi_lane'])
    threshold = config['threshold']
    mode_name = config['name']
    
    logger.info(f"[DETECTION] {mode_name} - Threshold: {threshold}")

    # OCR cache: {spot_idx: {'last': frame_count, 'text': str, 'prob': float}}
    ocr_cache = {}
    ocr_interval = 30  # frames between OCR attempts per spot

    # import OCR helpers lazily (avoid heavy import at module load)
    from parkingapp.number_plate_detection import (
        detect_numberplate_in_image,
        get_best_plate_text,
        draw_plate_text,
    )

    def check_parking_space(img_pro, img):
        space_counter = 0

        for idx, pos in enumerate(posList):
            x, y = pos

            # Crop parking space region from processed image for pixel counting
            img_crop = img_pro[y:y + height, x:x + width]

            # Count non-zero pixels (vehicles)
            count = cv2.countNonZero(img_crop)

            # Classify based on threshold
            if count < threshold:
                color = (0, 255, 0)  # Green for FREE
                thickness = 5
                space_counter += 1
            else:
                color = (0, 0, 255)  # Red for OCCUPIED
                thickness = 2

            # Draw rectangle around parking space
            cv2.rectangle(img, (x, y), (x + width, y + height), color, thickness)

            # Display pixel count for each space
            cvzone.putTextRect(img, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)

            # If occupied, attempt OCR every ocr_interval frames
            if count >= threshold:
                last = ocr_cache.get(idx, {}).get('last', -9999)
                if frame_count - last >= ocr_interval:
                    # Crop color ROI from original frame for OCR
                    try:
                        roi_color = img[y:y + height, x:x + width].copy()
                        plates = detect_numberplate_in_image(roi_color)
                        best = get_best_plate_text(plates)
                        if best and best.get('prob', 0.0) >= 0.25 and best.get('text', '').strip():
                            ocr_cache[idx] = {'last': frame_count, 'text': best['text'], 'prob': best['prob']}
                        else:
                            ocr_cache[idx] = {'last': frame_count, 'text': '', 'prob': 0.0}
                    except Exception:
                        ocr_cache[idx] = {'last': frame_count, 'text': '', 'prob': 0.0}

                # If we have cached plate text, draw it
                cached = ocr_cache.get(idx)
                if cached and cached.get('text'):
                    draw_plate_text(img, (x, y), cached.get('text'))

        # Display total free spaces and mode
        cvzone.putTextRect(img, f'Free: {space_counter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))
        cvzone.putTextRect(img, f'Mode: {mode_name}', (100, 120), scale=1.5, thickness=2, offset=10, colorR=(102, 126, 234))

    try:
        while cap.isOpened():
            success, img = cap.read()
            if not success:
                break

            # Image Processing Pipeline (standard, no adaptive)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
            img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
            img_median = cv2.medianBlur(img_threshold, 5)
            kernel = np.ones((3, 3), np.uint8)
            img_dilate = cv2.dilate(img_median, kernel, iterations=1)

            # Check parking spaces and draw results
            check_parking_space(img_dilate, img)

            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', img)
            if not ret:
                logger.error(f"Failed to encode frame {frame_count}")
                continue

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            frame_count += 1
            if frame_count % 30 == 0:
                logger.info(f"[INFO] Processed {frame_count} frames")

    except cv2.error as e:
        logger.error(f'OpenCV error: {e}')
    except IOError as e:
        logger.error(f'IO error: {e}')
    except Exception as e:
        logger.error(f'Error: {type(e).__name__}: {e}', exc_info=True)
    finally:
        if cap:
            cap.release()
        logger.info(f'Video processing complete. Total frames: {frame_count}')


def generate_frames(cap, posList):
    """Main video detection function for parking space monitoring"""
    width, height = 107, 48  # Parking space dimensions

    def check_parking_space(img_pro, img):
        """Check which parking spaces are free or occupied"""
        space_counter = 0

        for pos in posList:
            x, y = pos

            # Crop the region for each parking space
            img_crop = img_pro[y:y + height, x:x + width]
            count = cv2.countNonZero(img_crop)  # Count non-zero pixels

            # Determine if space is free or occupied
            if count < 900:
                color = (0, 255, 0)  # Green = Free
                thickness = 5
                space_counter += 1
            else:
                color = (0, 0, 255)  # Red = Occupied
                thickness = 2

            # Draw rectangle around parking space
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
            cvzone.putTextRect(img, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)

        # Display total free parking spaces
        cvzone.putTextRect(img, f'Free: {space_counter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))

    # Process video frames
    while cap.isOpened():
        success, img = cap.read()
        if not success:
            break

        # Image preprocessing pipeline
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)  # Blur for noise reduction
        img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)  # Threshold
        img_median = cv2.medianBlur(img_threshold, 5)  # Median blur
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(img_median, kernel, iterations=1)  # Dilate to enhance features

        # Check parking spaces
        check_parking_space(img_dilate, img)

        # Encode frame to JPEG and yield for streaming
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def VideoPage(request):
    """View handler for video streaming"""
    try:
        a = Upload_File.objects.last()
        if not a:
            return HttpResponse("No video uploaded. Please upload a video first.", status=400)
        
        print(a.Video, 'video path')
        b = str(a.Video)
        cap = cv2.VideoCapture('media/' + b)  # Load video file
        
        # Check if video capture was successful
        if not cap.isOpened():
            return HttpResponse("Failed to open video file. The file may be corrupted or in an unsupported format.", status=400)
        
        # Load parking space positions from pickle file
        with open('parkingapp/CarParkPos', 'rb') as f:
            posList = pickle.load(f)

        # Return streaming response
        return StreamingHttpResponse(generate_frames(cap, posList),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}")
        return HttpResponse(f"File not found error: {str(e)}", status=404)
    except Exception as e:
        print(f"[ERROR] VideoPage error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error processing video: {str(e)}", status=500)

def SmartParkingPage(request):
    if request.method == 'POST':
        # Check if file is uploaded
        if 'upload_file' not in request.FILES or not request.FILES['upload_file']:
            messages.error(request, 'Please upload a video file for parking analysis.')
            return render(request, 'smartcarparking.html')
        
        try:
            video = request.FILES['upload_file']
            detection_type = request.POST.get('detection_type', 'multi_lane')
            
            # Validate video file name
            if not video.name:
                messages.error(request, 'Invalid file name. Please upload a valid video file.')
                return render(request, 'smartcarparking.html')
            
            # Validate file size (max 100MB for videos)
            if video.size > 100 * 1024 * 1024:
                messages.error(request, 'Video file exceeds 100MB limit. Please upload a smaller video.')
                return render(request, 'smartcarparking.html')
            
            # Validate file size minimum (at least 100KB)
            if video.size < 100 * 1024:
                messages.error(request, 'Video file is too small. Please upload a valid video.')
                return render(request, 'smartcarparking.html')
            
            # Validate file type
            allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
            file_ext = video.name.lower().split('.')[-1]
            if f'.{file_ext}' not in allowed_extensions:
                messages.error(request, f'Invalid file format. Supported formats: {", ".join(allowed_extensions)}')
                return render(request, 'smartcarparking.html')
            
            # Validate detection type
            valid_detection_types = ['multi_lane', 'reserved_spot', 'night_vision', 'angled_spot']
            if detection_type not in valid_detection_types:
                messages.error(request, 'Invalid detection type selected.')
                return render(request, 'smartcarparking.html')
            
            # Create upload record with detection type
            upload_record = Upload_File.objects.create(Video=video)
            
            # Store detection type in session for processing
            request.session['detection_type'] = detection_type
            request.session['upload_id'] = upload_record.Video_Id
            
            detection_names = {
                'multi_lane': 'Multi-Lane Parking Detection',
                'reserved_spot': 'Reserved Spot Recognition',
                'night_vision': 'Night Vision Detection',
                'angled_spot': 'Angled Spot Tracking'
            }
            
            detection_name = detection_names.get(detection_type, 'Multi-Lane Parking Detection')
            messages.success(request, f'Smart Parking Analysis ({detection_name}) Executed Successfully...')
            logger.info(f'Video uploaded: {video.name} ({video.size} bytes) with detection type: {detection_type}')
            return redirect('video')
        
        except IOError as e:
            logger.error(f'IO error uploading video: {e}')
            messages.error(request, 'Error reading video file. Please try another file.')
            return render(request, 'smartcarparking.html')
        except Exception as e:
            logger.error(f'Error uploading video: {type(e).__name__}: {e}', exc_info=True)
            messages.error(request, f'Error uploading video. Please try again.')
            return render(request, 'smartcarparking.html')

    return render(request, 'smartcarparking.html')


# ============ PAYMENT SYSTEM VIEWS ============
def payment_page(request):
    """Display payment page"""
    from parkingapp.payment_service import PaymentService
    from parkingapp.models import Vehicle
    
    vehicles = Vehicle.objects.all()[:10]
    
    context = {
        'vehicles': vehicles,
        'pricing_tiers': {
            '1_hour': 5.00,
            '2_hours': 8.00,
            '4_hours': 15.00,
            'additional_hour': 3.00,
            'daily_max': 50.00
        }
    }
    return render(request, 'payment_page.html', context)


def calculate_parking_fee(request):
    """API endpoint to calculate parking fee"""
    from django.http import JsonResponse
    from parkingapp.payment_service import PaymentService
    from datetime import datetime
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entry_time_str = data.get('entry_time')
            exit_time_str = data.get('exit_time')
            
            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
            exit_time = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00'))
            
            fee = PaymentService.calculate_parking_fee(None, entry_time, exit_time)
            
            return JsonResponse({
                'success': True,
                'fee': float(fee),
                'currency': 'USD'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'POST required'}, status=400)


def process_parking_payment(request):
    """Process payment and send receipt"""
    from parkingapp.payment_service import PaymentService
    from parkingapp.email_service import EmailNotificationService
    from datetime import datetime
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            vehicle_id = data.get('vehicle_id')
            lot_id = data.get('lot_id')
            entry_time_str = data.get('entry_time')
            exit_time_str = data.get('exit_time')
            amount = data.get('amount')
            user_email = data.get('user_email')
            
            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
            exit_time = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00'))
            
            # Create invoice
            invoice = PaymentService.create_invoice(
                vehicle_id, lot_id, entry_time, exit_time, amount
            )
            
            # Process payment
            payment_result = PaymentService.process_payment(amount, vehicle_id, 'mock')
            
            if payment_result['success']:
                invoice.update(payment_result)
                
                # Send email receipt
                if user_email:
                    from parkingapp.models import Vehicle
                    try:
                        vehicle = Vehicle.objects.get(id=vehicle_id)
                        receipt = PaymentService.generate_receipt(
                            invoice,
                            {'plate': vehicle.license_plate, 'type': vehicle.vehicle_type}
                        )
                        EmailNotificationService.send_parking_receipt(
                            user_email, receipt, invoice
                        )
                    except:
                        pass
                
                return JsonResponse({
                    'success': True,
                    'invoice': invoice,
                    'message': 'Payment successful! Receipt sent to email.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Payment failed'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'POST required'}, status=400)


# ============ USER MANAGEMENT VIEWS ============
def manage_users(request):
    """Admin user management page"""
    from django.contrib.auth.models import User
    from parkingapp.rbac import RoleManager
    
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return redirect('login')
    
    users = User.objects.all()
    roles = RoleManager.ROLES
    
    context = {
        'users': users,
        'roles': roles
    }
    return render(request, 'manage_users.html', context)


def update_user_role(request):
    """Update user role via AJAX"""
    from django.contrib.auth.models import User
    from django.http import JsonResponse
    import json
    
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
            
            data = json.loads(request.body)
            user_id = data.get('user_id')
            role = data.get('role')
            
            user = User.objects.get(id=user_id)
            
            # Create or update profile
            if not hasattr(user, 'profile'):
                from parkingapp.models import UserProfile
                UserProfile.objects.create(user=user, role=role)
            else:
                user.profile.role = role
                user.profile.save()
            
            return JsonResponse({
                'success': True,
                'message': f'User role updated to {role}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'POST required'}, status=400)


# ============ RECEIPT/INVOICE VIEW ============
def view_receipt(request, invoice_id):
    """Display receipt/invoice"""
    context = {
        'invoice_id': invoice_id,
        'details': {
            'vehicle': 'ABC-1234',
            'entry': '2024-01-15 10:30 AM',
            'exit': '2024-01-15 2:45 PM',
            'duration': '4 hrs 15 min',
            'amount': '₹2,167.50',
            'status': 'PAID',
            'transaction_id': 'TXN-ABC123'
        }
    }
    return render(request, 'receipt.html', context)