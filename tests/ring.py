from PIL import Image, ImageDraw

# Parameters for the ring
center = (150, 150)  # Center coordinates
radius = 100  # Outer radius
width = 20  # Width of the ring

# Create a new image
image = Image.new("RGB", (300, 300), "white")
draw = ImageDraw.Draw(image)

# Draw the ring
draw.ellipse(
    (
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius,
    ),
    outline="black",
    width=width,
)

# Save or display the image
image.show()
