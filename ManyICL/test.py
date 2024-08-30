import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Read the image file
image = mpimg.imread('C:\\Users\\JeffreyGoldberg\\Documents\\VS Code\\ManyICL_Demo\\ManyICL\\dataset\\CheXpert\\images\\chexpert_test_df\\CheXpert-v1.0 batch 3 (train 2)\\patient27438\\study1\\view1_frontal.jpg')

# Display the image
plt.imshow(image)
plt.axis('off')  # Hide axis
plt.show()