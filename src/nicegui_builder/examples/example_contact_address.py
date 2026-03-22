from nicegui import ui
from pydantic import BaseModel, Field
from nicegui_builder import form
import typing as t

Civility = t.Literal["Mr.", "Miss", "Ms.", "Sir"]


class ContactAddress(BaseModel):

    civility: Civility = Field(
        default="Mr.",
        title="Civility",
        description="The polite address",
        examples=["Mr.", "Sir", "Ms."],
    )

    fullname: str = Field(
        default="",
        title="Full name",
        description="The full name",
        examples=["Mark Carney", "Keir Starmer", "Alex Morgan"],
    )

    address: str = Field(
        default="",
        title="Address line",
        description="The door number, the street and the suite",
        examples=["1 Sussex Drive", "10 Downing Street", "55 Orchard Avenue"],
    )

    city: str = Field(
        default="",
        title="City",
        description="The city",
        examples=["Ottawa", "London", "Boston"],
    )
    
    province: str = Field(
        default="",
        title="Province",
        description="The province",
        examples=["Quebec", "", ""],
    )

    postalcode: str = Field(
        default="",
        title="Postal code",
        description="The postal code",
        examples=["K1A 0A1", "SW1A 2AA", "75008"],
    )

    country: str = Field(
        default="",
        title="Country",
        description="The country",
        examples=["Canada", "United Kingdom", "France"],
    )


contact_address = ContactAddress()


def build_ui():
    ui.label("Hello from NiceGUI 👋")
    form(contact_address)


def main(*, port: int = 8080, host: str | None = None, reload: bool = True):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
