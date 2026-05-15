import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue

# Set up a thread-safe queue to store detected barcode data
result_queue = queue.Queue()


def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")

    # Decode barcodes from the frame
    barcodes = decode(img)

    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type

        # Put the data into the queue for the main thread to read
        result_queue.put(f"{barcode_type}: {barcode_data}")

        # Draw a bounding box on the video frame
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, barcode_data, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")


st.title("Mobile Barcode Scanner")

# WebRTC Streamer configuration
ctx = webrtc_streamer(
    key="barcode-scanner",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_frame_callback,
    # media_stream_constraints are vital for mobile camera selection
    media_stream_constraints={
        "video": {"facingMode": "environment"},  # Requests back camera
        "audio": False
    },
    async_processing=True,
)

# UI to display the results from the queue
st.subheader("Scanned Results:")
result_placeholder = st.empty()

while ctx.state.playing:
    try:
        # Get data from the queue without blocking
        result = result_queue.get(timeout=1.0)
        st.write(f"✅ Found: {result}")
    except queue.Empty:
        continue
