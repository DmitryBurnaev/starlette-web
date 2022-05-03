from starlette.routing import Route, Mount
from starlette_web.contrib.auth import views

routes = [
    Mount(
        "/auth",
        routes=[
            Route("/me/", views.ProfileApiView),
            Route("/sign-in/", views.SignInAPIView),
            Route("/sign-up/", views.SignUpAPIView),
            Route("/sign-out/", views.SignOutAPIView),
            Route("/refresh-token/", views.RefreshTokenAPIView),
            Route("/invite-user/", views.InviteUserAPIView),
            Route("/reset-password/", views.ResetPasswordAPIView),
            Route("/change-password/", views.ChangePasswordAPIView),
        ],
    )
]
