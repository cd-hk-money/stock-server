from fastapi import FastAPI
import py_eureka_client.eureka_client as ec
import uvicorn

app = FastAPI(title="Eureka-Py")

rest_port = 8050
ec.init(eureka_server="http://localhost:8761",
        app_name="stock-service",
        instance_port=rest_port)

if __name__ == '__main__':
    uvicorn.run(app="test:app", port=8050, reload=True)