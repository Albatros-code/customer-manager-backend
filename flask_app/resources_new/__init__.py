from .auth import (
    UserRegistration,
    UserLogin,
    UserLogoutAccess,
    UserLogoutRefresh,
    UserEmailVerify,
    TokenRefresh,
    PasswordResetPasswordChange,
    PasswordResetSendEmail,
)

from .users import (
    Users,
    User,
    UserAppointments,
)

from .appointments import (
    Appointments
)

from .services import (
    Services
)

from .available_dates import (
    AvailableDates
)

from .settings import (
    Settings,
    SettingsDefault,
)

resources = [
    (UserRegistration, '/registration'),
    (UserLogin, '/login'),
    (UserLogoutAccess, '/logout/access'),
    (UserLogoutRefresh, '/logout/refresh'),
    (TokenRefresh, '/token/refresh'),
    (UserEmailVerify, '/registration/<string:email_verification_string>'),
    (PasswordResetSendEmail, '/password-reset/send-email'),
    (PasswordResetPasswordChange, '/password-reset/change-password'),

    (Users, '/users'),
    (User, '/users/<string:id>'),
    (UserAppointments, '/users/<string:id>/appointments'),

    (Appointments, '/appointments'),

    (Services, '/services'),

    (AvailableDates, '/available-dates'),

    (Settings, '/settings'),
    (SettingsDefault, '/settings/default')
]

