from PIL import Image
import json

filename = "test.png"

image = Image.open(filename)

print("Metadata keys:")
print(image.text.keys())

print()

if "Radek MSc" in image.text:

    metadata = json.loads(image.text["Radek MSc"])

    print("Metadata found:\n")

    print(json.dumps(metadata, indent=4))

else:
    print("No Toolery metadata found.")

image.show()