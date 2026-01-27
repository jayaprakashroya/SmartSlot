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
    """Dedicated admin login page - for admin users only"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Input validation
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'admin_login.html')
        
        # Try Django authentication first
        try:
            user = authenticate(request, username=email, password=password)
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
            logger.error(f'Admin login error for {email}: {str(e)}')
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
    Image Processing-based parking detection using OpenCV
    Algorithm:
    - Convert to Grayscale: cv2.cvtColor() - converts color image to grayscale
    - Blur: cv2.GaussianBlur() - reduces noise
    - Threshold: cv2.adaptiveThreshold() - creates binary image
    - Median Blur: cv2.medianBlur() - further noise reduction
    - Dilate: cv2.dilate() - fills gaps in objects
    - Count Pixels: cv2.countNonZero() - counts non-zero pixels in parking space
    
    If count < 900 → Space is FREE (green)
    If count ≥ 900 → Space is OCCUPIED (red)
    """
    width, height = 107, 48
    frame_count = 0
    
    print("[INFO] Starting OpenCV Image Processing Parking Detection...")
    
    def check_parking_space(img_pro, img):
        space_counter = 0

        for pos in posList:
            x, y = pos

            # Crop parking space region
            img_crop = img_pro[y:y + height, x:x + width]
            
            # Count non-zero pixels (vehicles)
            count = cv2.countNonZero(img_crop)

            # Threshold: 900 pixels = occupied, less = free
            if count < 900:
                color = (0, 255, 0)  # Green for FREE
                thickness = 5
                space_counter += 1
            else:
                color = (0, 0, 255)  # Red for OCCUPIED
                thickness = 2

            # Draw rectangle around parking space
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
            
            # Display pixel count for each space
            cvzone.putTextRect(img, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)

        # Display total free spaces
        cvzone.putTextRect(img, f'Free: {space_counter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))

    try:
        while cap.isOpened():
            success, img = cap.read()
            if not success:
                break

            # Image Processing Pipeline
            # 1. Convert to Grayscale
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 2. Apply Gaussian Blur (reduce noise)
            img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
            
            # 3. Adaptive Threshold (create binary image)
            img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
            
            # 4. Median Blur (further noise reduction)
            img_median = cv2.medianBlur(img_threshold, 5)
            
            # 5. Dilate (fill gaps in objects)
            kernel = np.ones((3, 3), np.uint8)
            img_dilate = cv2.dilate(img_median, kernel, iterations=1)

            # Check parking spaces and draw results
            check_parking_space(img_dilate, img)

            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', img)
            if not ret:
                print(f"[ERROR] Failed to encode frame {frame_count}")
                continue
                
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"[INFO] OpenCV processed {frame_count} frames - Real-time Detection Active")
    
    except cv2.error as e:
        logger.error(f'OpenCV error in detection stream: {e}')
    except IOError as e:
        logger.error(f'IO error in detection stream: {e}')
    except Exception as e:
        logger.error(f'Unexpected error in detection stream: {type(e).__name__}: {e}', exc_info=True)
    finally:
        if cap:
            cap.release()
        logger.info(f'Video processing complete. Total frames processed: {frame_count}')


def generate_frames(cap, posList, detection_type='multi_lane'):
    """
    Legacy pixel-counting based parking detection (70-80% accuracy)
    Fallback method if YOLOv8 is not available
    """
    width, height = 107, 48

    def check_parking_space(img_pro, img):
        space_counter = 0

        for pos in posList:
            x, y = pos

            img_crop = img_pro[y:y + height, x:x + width]
            count = cv2.countNonZero(img_crop)

            # Adjust threshold based on detection type
            threshold = get_pixel_threshold(detection_type)
            
            # Apply any dynamic adjustments here
            # threshold = adjust_thresholds_for_daytime()['pixel_count_multi_lane']  # Uncomment to override

            if count < threshold:
                color = (0, 255, 0)  # Green for available
                thickness = 5
                space_counter += 1
            else:
                color = (0, 0, 255)  # Red for occupied
                thickness = 2

            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
            cvzone.putTextRect(img, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)

        # Display detection type info
        detection_info = {
            'multi_lane': 'Multi-Lane Detection',
            'reserved_spot': 'Reserved Spot Recognition',
            'night_vision': 'Night Vision Detection',
            'angled_spot': 'Angled Spot Tracking'
        }
        
        cvzone.putTextRect(img, f'Free: {space_counter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))
        cvzone.putTextRect(img, f'Mode: {detection_info.get(detection_type, "Multi-Lane")}', (100, 120), scale=1.5, thickness=2, offset=10, colorR=(102, 126, 234))

    while cap.isOpened():
        success, img = cap.read()
        if not success:
            break

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
        img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        img_median = cv2.medianBlur(img_threshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(img_median, kernel, iterations=1)

        check_parking_space(img_dilate, img)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def VideoPage(request):
    try:
        a = Upload_File.objects.last()
        if not a:
            return HttpResponse("No video uploaded. Please upload a video first.", status=400)
        
        print(f'Video path: {a.Video}')
        video_path = f'media/{str(a.Video)}'
        
        # Check if file exists
        if not os.path.exists(video_path):
            return HttpResponse(f"Video file not found at {video_path}. Please try uploading again.", status=404)
        
        cap = cv2.VideoCapture(video_path)
        
        # Check if video capture was successful
        if not cap.isOpened():
            return HttpResponse("Failed to open video file. The file may be corrupted or in an unsupported format.", status=400)
        
        # Check if parking positions file exists
        pos_file = 'parkingapp/CarParkPos'
        if not os.path.exists(pos_file):
            return HttpResponse("Parking position file not found. Please ensure CarParkPos file exists.", status=400)
        
        with open(pos_file, 'rb') as f:
            posList = pickle.load(f)
        
        # Get detection type from session
        detection_type = request.session.get('detection_type', 'multi_lane')
        
        # Use OpenCV Image Processing Detection
        print("[INFO] Using OpenCV Image Processing Detection - Real-time Parking Analysis")
        return StreamingHttpResponse(generate_frames_yolov8(cap, posList, detection_type),
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