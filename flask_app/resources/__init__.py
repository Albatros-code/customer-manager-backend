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
    Appointments,
    Appointment,
)

from .services import (
    Services
)

from .available_dates import (
    AvailableDates
)

from .available_hours import (
    AvailableSlots
)

from .settings import (
    Settings,
    SettingsDefault,
)

from .util import (
    CurrentDate
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
    (Appointment, '/appointment/<string:id>'),

    (Services, '/services'),

    (AvailableDates, '/available-dates'),

    (AvailableSlots, '/available-slots'),

    (Settings, '/settings'),
    (SettingsDefault, '/settings/default'),

    (CurrentDate, '/util/current-date')
]

