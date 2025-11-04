from gradio_client import Client, handle_file

client = Client("Godslayer98465/cnn")

try:
    result = client.predict(
        image_pil=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
        api_name="/predict"
    )

    predicted_class, processed_image_path = result
    
    print(result[0]['confidences'][0]['confidence'])
    print(result[0]['label'])
    print(processed_image_path)

except Exception as e:
    print(f"An error occurred: {e}")