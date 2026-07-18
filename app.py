import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Non-Invasive Anemia Screener", layout="centered")

st.title("🩸 Multimodal Anemia Screening Portal")
st.write("Upload clear photos of your lower eyelid conjunctiva, nail beds, or tongue for an instant risk analysis.")

# Create columns for the three target regions
col1, col2, col3 = st.columns(3)

uploaded_files = {}

with col1:
    st.subheader("👁️ Eyelid")
    eye_file = st.file_uploader("Upload Conjunctiva", type=["jpg", "jpeg", "png"], key="eye")
    if eye_file:
        uploaded_files["Conjunctiva"] = Image.open(eye_file)
        st.image(uploaded_files["Conjunctiva"], use_container_width=True)

with col2:
    st.subheader("💅 Nail Beds")
    nail_file = st.file_uploader("Upload Nails", type=["jpg", "jpeg", "png"], key="nail")
    if nail_file:
        uploaded_files["Nail Bed"] = Image.open(nail_file)
        st.image(uploaded_files["Nail Bed"], use_container_width=True)

with col3:
    st.subheader("👅 Tongue")
    tongue_file = st.file_uploader("Upload Tongue", type=["jpg", "jpeg", "png"], key="tongue")
    if tongue_file:
        uploaded_files["Tongue"] = Image.open(tongue_file)
        st.image(uploaded_files["Tongue"], use_container_width=True)

st.markdown("---")

# Screening Trigger Button
if st.button("Run Multimodal Risk Assessment", type="primary"):
    if not uploaded_files:
        st.warning("Please upload at least one image to begin screening.")
    else:
        with st.spinner("Analyzing physiological markers..."):
            # Placeholder for your image processing / ML fusion logic
            # Right now, we simulate a baseline response
            mock_probability = 35.0 
            
            st.metric(label="Estimated Anemia Risk Probability", value=f"{mock_probability}%")
            
            if mock_probability < 30:
                st.success("Low Risk Indicated.")
            elif mock_probability < 70:
                st.warning("Moderate Risk Indicated. Consider tracking dietary iron intake.")
            else:
                st.error("High Risk Indicated. Clinical evaluation is recommended.")

st.markdown("---")
st.caption("⚠️ **Safety Notice & Disclaimer:** This application is a conceptual screening prototype built for educational hackathon purposes. It is not a medical device, does not provide clinical diagnoses, and should never replace professional medical evaluations.")
