import cv2


def rotate_if_needed(image):
    """
    Rotates landscape images to portrait.
    """

    height, width = image.shape[:2]

    if width > height:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    return image