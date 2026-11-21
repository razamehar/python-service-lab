from fastapi import FastAPI

app = FastAPI(
    title="AWS CI/CD Demo",
    description="A Python API demonstrating automated deployment to AWS.",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Check whether the application is running."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Return the application welcome message."""
    return {"message": "Welcome to the AWS CI/CD Demo API"}