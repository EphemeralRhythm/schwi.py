from PIL import Image, ImageDraw

# Load the input image
input_image = Image.open("images/profile.jpg")  # Replace with your image file

# Calculate the dimensions for the circular image
size = min(input_image.size)
output_image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
mask = Image.new("L", (size, size), 0)
draw_mask = ImageDraw.Draw(mask)
draw_mask.ellipse((0, 0, size, size), fill=255)

# Resize the input image to match the size of the circular mask
resized_input_image = input_image.resize((size, size))

# Apply the circular mask to the resized input image
circular_image = Image.new("RGBA", (size, size))
circular_image.paste(resized_input_image, (0, 0), mask)

# Save or display the circular image
# circular_image.show()
circular_image.save("circular_image.png")
