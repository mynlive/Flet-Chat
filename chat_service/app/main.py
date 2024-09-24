# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api import users, chats, messages, auth
from app.config import AppConfig
from app.infrastructure.database import Database
from app.infrastructure.event_dispatcher import EventDispatcher
from app.infrastructure.event_handlers import EventHandlers
from app.infrastructure.redis_config import RedisClient
from app.infrastructure.security import SecurityService

class Application:
    def __init__(self, config: AppConfig, database: Database = None):
        self.config = config
        self.database = database if database else Database(config.DATABASE_URL)
        self.redis_client = RedisClient(config.REDIS_HOST, config.REDIS_PORT)
        self.event_dispatcher = EventDispatcher()
        self.security_service = SecurityService(config)
        self.event_handlers = EventHandlers(self.redis_client)

        # Register event handlers
        self.event_dispatcher.register("MessageCreated", self.event_handlers.publish_message_created)
        self.event_dispatcher.register("MessageUpdated", self.event_handlers.publish_message_updated)
        self.event_dispatcher.register("MessageDeleted", self.event_handlers.publish_message_deleted)
        self.event_dispatcher.register("MessageStatusUpdated", self.event_handlers.publish_message_status_updated)
        self.event_dispatcher.register("UnreadCountUpdated", self.event_handlers.publish_unread_count_updated)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.database.connect()
        await self.redis_client.connect()
        yield
        await self.database.disconnect()
        await self.redis_client.disconnect()

    def create_app(self):
        app = FastAPI(
            title=self.config.PROJECT_NAME,
            version=self.config.PROJECT_VERSION,
            description=self.config.PROJECT_DESCRIPTION,
            openapi_url=f"{self.config.API_V1_STR}/openapi.json",
            lifespan=self.lifespan
        )

        app.state.config = self.config
        app.state.security_service = self.security_service
        app.state.event_dispatcher = self.event_dispatcher
        app.state.database = self.database

        # Create routers
        app.include_router(auth.create_router(), prefix=f"{self.config.API_V1_STR}/auth", tags=["auth"])
        app.include_router(users.create_router(), prefix=f"{self.config.API_V1_STR}/users", tags=["users"])
        app.include_router(chats.create_router(), prefix=f"{self.config.API_V1_STR}/chats", tags=["chats"])
        app.include_router(messages.create_router(), prefix=f"{self.config.API_V1_STR}/messages", tags=["messages"])

        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content={"message": f"An unexpected error occurred: {str(exc)}"}
            )

        @app.get("/")
        async def root():
            return {"message": "Welcome to the Chat API"}

        return app

def create():
    config = AppConfig()
    application = Application(config)
    return application.create_app()

app = create()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)