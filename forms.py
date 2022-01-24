from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length, NumberRange, Email, Optional
from flask_wtf import FlaskForm


class createPlaylistForm(FlaskForm):
    """Login form."""

    playlist_name = StringField(
        "Playlist Name",
        validators=[InputRequired(), Length(min=1, max=20)])


   
