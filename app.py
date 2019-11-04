import cv2
import os
import sys
import numpy
import pickle
import matplotlib.pyplot as plt
from enhance import image_enhance
from skimage.morphology import skeletonize, thin


# create former to pickle
def define_former(images, path):
	images_dict = {}
	for img_name in images:
		img = cv2.imread(path + img_name, cv2.IMREAD_GRAYSCALE)
		kp, des = get_descriptors(img)
		images_dict[img_name] = [kp, des, img]
  
	return images_dict


# pickle
# the array "images" must have the names of all images in the path/to/images directory
def serializes(images, path, filename):
	outfile = open("cache/" + filename, 'wb')
	former = define_former(images, path) 
	pickle.dump(former, outfile)
	outfile.close()


# unpickle
# images_dict format:
# images_dict = { image_name : [kp, des, img]}
def deserializes(filename):
	infile = open("cache/" + filename, 'rb')
	images_dict = pickle.load(infile)
	infile.close()
	return images_dict


def removedot(invertThin):
    temp0 = numpy.array(invertThin[:])
    temp0 = numpy.array(temp0)
    temp1 = temp0 / 255
    temp2 = numpy.array(temp1)
    temp3 = numpy.array(temp2)

    enhanced_img = numpy.array(temp0)
    filter0 = numpy.zeros((10, 10))
    W, H = temp0.shape[:2]
    filtersize = 6

    for i in range(W - filtersize):
        for j in range(H - filtersize):
            filter0 = temp1[i:i + filtersize, j:j + filtersize]

            flag = 0
            if sum(filter0[:, 0]) == 0:
                flag += 1
            if sum(filter0[:, filtersize - 1]) == 0:
                flag += 1
            if sum(filter0[0, :]) == 0:
                flag += 1
            if sum(filter0[filtersize - 1, :]) == 0:
                flag += 1
            if flag > 3:
                temp2[i:i + filtersize, j:j +
                      filtersize] = numpy.zeros((filtersize, filtersize))

    return temp2


def get_descriptors(img):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)
    img = image_enhance.image_enhance(img)
    img = numpy.array(img, dtype=numpy.uint8)
    # Threshold
    ret, img = cv2.threshold(
        img, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    # Normalize to 0 and 1 range
    img[img == 255] = 1

    # Thinning
    skeleton = skeletonize(img)
    skeleton = numpy.array(skeleton, dtype=numpy.uint8)
    skeleton = removedot(skeleton)
    # Harris corners
    harris_corners = cv2.cornerHarris(img, 3, 3, 0.04)
    harris_normalized = cv2.normalize(
        harris_corners,
        0,
        255,
        norm_type=cv2.NORM_MINMAX,
        dtype=cv2.CV_32FC1)
    threshold_harris = 125
    # Extract keypoints
    keypoints = []
    for x in range(0, harris_normalized.shape[0]):
        for y in range(0, harris_normalized.shape[1]):
            if harris_normalized[x][y] > threshold_harris:
                keypoints.append(cv2.KeyPoint(y, x, 1))
    # Define descriptor
    orb = cv2.ORB_create()
    # Compute descriptors
    _, des = orb.compute(img, keypoints)
    return (keypoints, des)


def main():
    image_name = sys.argv[1]
    samples = helpers.deserializes('cache/samples_processed')
    kp1, des1, img1 = samples[image_name][0], samples[image_name][1], samples[image_name][2]
    # image_path = "database/samples/" + image_name
    # img1 = cv2.imread(image_path , cv2.IMREAD_GRAYSCALE)
    # kp1, des1 = get_descriptors(img1)

    image_name = sys.argv[2]
    permitted = helpers.deserializes('cache/permitted_processed')
    kp2, des2, img2 = permitted[image_name][0], permitted[image_name][1], permitted[image_name][2]
    # image_path = "database/permitted/" + image_name
    # img2 = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # kp2, des2 = get_descriptors(img2)

    # Matching between descriptors
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = sorted(bf.match(des1, des2), key=lambda match: match.distance)
    # Plot keypoints
    img4 = cv2.drawKeypoints(img1, kp1, outImage=None)
    img5 = cv2.drawKeypoints(img2, kp2, outImage=None)
    f, axarr = plt.subplots(1, 2)
    axarr[0].imshow(img4)
    axarr[1].imshow(img5)
    plt.show()
    # Plot matches
    img3 = cv2.drawMatches(img1, kp1, img2, kp2, matches, flags=2, outImg=None)
    plt.imshow(img3)
    plt.show()

    # Calculate score
    score = 0
    for match in matches:
        score += match.distance
    score_threshold = 33
    if score / len(matches) < score_threshold:
        print("Fingerprint matches.")
    else:
        print("Fingerprint does not match.")


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        raise