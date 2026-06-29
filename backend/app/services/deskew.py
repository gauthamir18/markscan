import cv2
import numpy as np


def deskew_image(image):
    """
    Straightens a tilted document using the largest contour.
    Returns the corrected image.
    """

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur to remove noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Binary image
    thresh = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]

    # Find contours
    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return image

    # Largest contour (should be the answer sheet)
    largest = max(contours, key=cv2.contourArea)

    rect = cv2.minAreaRect(largest)

    angle = rect[-1]

    # Convert OpenCV angle
    if angle < -45:
        angle = 90 + angle

    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return rotated