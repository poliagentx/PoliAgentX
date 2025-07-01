# Static Site Project

This project is a simple static website that serves HTML and CSS files using Docker.

## Project Structure

```
static-site-project
├── public
│   ├── index.html
│   └── styles.css
├── Dockerfile
└── README.md
```

## Getting Started

To build and run this project, you need to have Docker installed on your machine.

### Building the Docker Image

Navigate to the project directory and run the following command to build the Docker image:

```
docker build -t static-site .
```

### Running the Docker Container

After building the image, you can run the container using the following command:

```
docker run -d -p 8080:80 static-site
```

This command will start the container in detached mode and map port 80 of the container to port 8080 on your host machine.

### Accessing the Website

Open your web browser and go to `http://localhost:8080` to view the static website.

## License

This project is licensed under the MIT License.