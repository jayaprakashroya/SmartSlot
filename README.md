# SmartSlot - AI-Powered Smart Car Parking System

A comprehensive Django-based intelligent parking management system using YOLOv8 AI for real-time vehicle detection, occupancy tracking, and advanced parking analytics.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-3.2+-green.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Latest-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Features

### Core Features
- **Real-time Vehicle Detection**: YOLOv8 AI-powered vehicle detection and classification
- **Parking Occupancy Tracking**: Real-time parking spot occupancy monitoring
- **License Plate Recognition**: Automatic vehicle identification via license plates
- **Interactive Parking Map**: Visual representation of parking lot with real-time status
- **User Management**: Customer and admin authentication with role-based access

### Advanced Features
- **Analytics Dashboard**: Comprehensive parking analytics and insights
- **Heatmap Visualization**: Peak hours and parking patterns analysis
- **Reservation System**: Online parking spot reservation
- **Payment Integration**: Online payment processing for parking fees
- **Find My Vehicle**: Locate your parked vehicle on the map
- **Notifications**: Real-time alerts for parking events
- **Revenue Reports**: Financial analytics for parking operators
- **Offline Mode**: Progressive Web App (PWA) support

### AI & Detection Features
- **Multi-Lane Parking Detection**: Detect vehicles in multiple parking lanes
- **Night Vision Detection**: Enhanced detection in low-light conditions
- **Angled Spot Tracking**: Handle vehicles in angled parking spots
- **Reserved Spot Recognition**: Identify and enforce reserved parking spots
- **Edge Case Handling**: Robust handling of various parking scenarios

## 📋 Technology Stack

### Backend
- **Framework**: Django 3.2+
- **Database**: SQLite3 / PostgreSQL
- **AI/ML**: YOLOv8 (Ultralytics)
- **Computer Vision**: OpenCV
- **API**: Django REST Framework

### Frontend
- **HTML/CSS/JavaScript**: Bootstrap 4+
- **Templates**: Django Templates
- **Maps**: Google Maps API
- **Charts**: Chart.js, Owl Carousel

### Deployment
- **Server**: Gunicorn/uWSGI
- **Web Server**: Nginx
- **Containerization**: Docker (optional)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jayaprakashroya/SmartSlot.git
cd SmartSlot
```

2. **Create and activate virtual environment**
```bash
# On Windows
python -m venv myenv
myenv\Scripts\activate

# On macOS/Linux
python3 -m venv myenv
source myenv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r Requirements.txt
```

4. **Download YOLOv8 Models**
The project uses YOLOv8 models for vehicle detection. Models are automatically downloaded on first use, or manually download:
```bash
# Download nano model (smallest, fastest)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Download medium model (balanced)
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
```

5. **Database Setup**
```bash
cd c:\Users\maner\Downloads\SmartSlot\myenv\Smart-car-parking
python manage.py migrate
python manage.py createsuperuser
python populate_sample_data.py  # Optional: Load sample data
```

6. **Run Development Server**
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

## � Project Structure

```
SmartSlot/
├── ParkingProject/          # Django project settings
│   ├── settings.py          # Project configuration
│   ├── urls.py              # URL routing
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── parkingapp/              # Main Django application
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── admin_views.py       # Admin dashboard views
│   ├── yolov8_detector.py   # YOLOv8 detection engine
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, Images
├── assets/                  # Static assets
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript files
│   └── images/              # Image assets
├── templates/               # Global templates
├── manage.py                # Django management script
├── Requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🎮 Usage

### For Users
1. **Sign Up**: Create an account as a customer
2. **View Parking Map**: See available parking spots in real-time
3. **Reserve Parking**: Book a parking spot in advance
4. **Make Payment**: Pay parking fees through the platform
5. **Track Vehicle**: Use "Find My Vehicle" to locate your car
6. **View History**: Check your parking history and analytics

### For Administrators
1. **Login**: Access admin dashboard with credentials 
2. **Monitor Parking**: Real-time occupancy monitoring
3. **Manage Users**: User account management
4. **View Analytics**: Parking patterns, revenue, and statistics
5. **Handle Disputes**: Resolve parking disputes
6. **Configuration**: System settings and parking lot configuration

### Running Detection
```bash
# Run vehicle detection on video
python run_with_yolov8.py

# Test detection on image
python test_detection.py
```

## 🔧 Configuration

Edit `parkingapp/detection_config.py` to customize:
- Detection confidence thresholds
- Model selection (nano, small, medium, large)
- Parking lot grid configuration
- Alert settings

## 📊 Key APIs

### Parking Occupancy
- `GET /api/parking-status/` - Get parking occupancy data
- `GET /api/parking-heatmap/` - Get heatmap visualization data

### Reservations
- `POST /api/reserve-parking/` - Create reservation
- `GET /api/my-reservations/` - Get user reservations

### Vehicle Detection
- `GET /api/vehicle-history/` - Vehicle entry/exit history
- `POST /api/detect-vehicle/` - Trigger detection

## 🧪 Testing

Run the test suite:
```bash
python manage.py test

# Specific test file
python test_detection.py
python test_occupancy_simple.py
```

## 🛣️ Roadmap

- [ ] Mobile app (iOS/Android)
- [ ] Machine learning for demand prediction
- [ ] Integration with IoT sensors
- [ ] EV charging station integration
- [ ] Multi-location support
- [ ] Advanced analytics with Tableau
- [ ] License plate payment integration

## 🐛 Edge Cases Handled

The system is designed to handle:
- ✅ Vehicles partially in/out of parking spots
- ✅ Overlapping parking spot detections
- ✅ Night and low-light conditions
- ✅ Angled parking spots
- ✅ Reserved and disabled spots
- ✅ Multiple vehicle entries in one frame
- ✅ Vehicles with different sizes and orientations

## 📝 Documentation

Detailed guides available:
- [TECHNOLOGY_STACK_GUIDE.md](TECHNOLOGY_STACK_GUIDE.md) - Tech stack details
- [COMPLETE_PROJECT_GUIDE.md](COMPLETE_PROJECT_GUIDE.md) - Full project documentation
- [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md) - Architecture overview
- [SMART_PARKING_SYSTEM_GUIDE.md](SMART_PARKING_SYSTEM_GUIDE.md) - System guide
- [VIVA_VOICE_EXAM_QA.md](VIVA_VOICE_EXAM_QA.md) - FAQ and Q&A

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Authors

- **Developers**:  
Shaik Baba Vali 22KF1A05B2
Maneri Jaya Prakash 22KF1A0573           Jayaprakash Roya — https://github.com/jayaprakashroya — manerijayaprakash@gmail.com  
Mallepogula Ganesh 22KF1A0571
Nese Anil 22KF1A0586
Palla Jayaprakash Babu 23KF5A0510 
- **AI Framework**: YOLOv8 by Ultralytics
- **Framework**: Django by Django Software Foundation

##  Acknowledgments

- YOLOv8 by Ultralytics for the powerful object detection framework
- Django community for the robust web framework
- Bootstrap for responsive UI components
- OpenCV for computer vision capabilities

## 📞 Support

For support, email or open an issue on GitHub.

## 🔐 Security Notes

- Change the Django secret key before deployment
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement rate limiting on APIs
- Use strong passwords for admin accounts
- Regularly update dependencies

## 🎓 Educational Purpose

This project is designed for educational purposes as a BTech final year project. It demonstrates:
- Full-stack web development with Django
- AI/ML integration (YOLOv8)
- Real-time data processing
- Database design and optimization
- RESTful API design
- Frontend-backend integration
- System architecture and design patterns

---

**Made with ❤️ for smart parking solutions**
