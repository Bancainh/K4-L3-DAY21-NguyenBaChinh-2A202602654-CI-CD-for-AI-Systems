from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import boto3
import joblib
import os


app = FastAPI()

ARTIFACT_BUCKET = os.environ["ARTIFACT_BUCKET"]
MODEL_KEY = "artifacts/current/model.joblib"
MODEL_PATH = os.path.expanduser("~/models/model.joblib")


def download_model():
    """Download the current model using the AWS default credential chain."""
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    s3 = boto3.client("s3")
    s3.download_file(
        ARTIFACT_BUCKET,
        MODEL_KEY,
        MODEL_PATH,
    )

    print(
        f"Downloaded s3://{ARTIFACT_BUCKET}/{MODEL_KEY} "
        f"to {MODEL_PATH}"
    )


download_model()
model = joblib.load(MODEL_PATH)


class ScoreRequest(BaseModel):
    features: list[float]


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    if len(req.features) != 10:
        raise HTTPException(
            status_code=400,
            detail="Expected exactly 10 features",
        )

    prediction = int(model.predict([req.features])[0])

    label = (
        "thu_nhap_cao"
        if prediction == 1
        else "thu_nhap_thap"
    )

    return {
        "prediction": prediction,
        "label": label,
    }


def main():
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
    )


if __name__ == "__main__":
    main()
