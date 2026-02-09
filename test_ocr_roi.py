import pickle, cv2
from parkingapp.number_plate_detection import detect_numberplate_in_image, get_best_plate_text

pos = pickle.load(open('parkingapp/CarParkPos','rb'))
print('Loaded', len(pos), 'positions')
cap = cv2.VideoCapture('media/sample_parking_lot.mp4')
if not cap.isOpened():
    print('Cannot open sample video')
    raise SystemExit(1)

ok, frame = cap.read()
if not ok:
    print('Cannot read frame')
    raise SystemExit(1)

x,y = pos[0]
w,h = 107,48
roi = frame[y:y+h, x:x+w]
print('ROI shape', roi.shape)
plates = detect_numberplate_in_image(roi)
print('Plates:', plates)
best = get_best_plate_text(plates)
print('Best:', best)
cap.release()
