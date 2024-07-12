from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/receiveData', methods=['POST'])
def receive_data():
    try:
        # Get data from the request
        data = request.data.decode('utf-8')

        # Process and store the data in a JSON file
        file_path = 'received_data.json'
        with open(file_path, 'r+') as file:
            content = file.read()

            if content.strip():  # Check if the file is not empty
                content = content.rstrip(']\n')  # Remove the trailing ']\n'
                file.seek(0)
                file.write(content + ',' + data + ']\n')
            else:
                file.write('[' + data + ']\n')

        print("Data received and saved:", data)

        return "Data received successfully"
    except Exception as e:
        print("Error:", str(e))
        return "Error processing data"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
