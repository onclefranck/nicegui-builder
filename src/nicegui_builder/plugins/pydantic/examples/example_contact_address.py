from nicegui import ui
from pydantic import BaseModel, Field
import nicegui_builder
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
        examples=["Jordan Lee", "Taylor Brooks", "Alex Morgan"],
    )

    address: str = Field(
        default="",
        title="Address line",
        description="The door number, the street and the suite",
        examples=["142 Willow Crest Lane", "27 Maple Court, Suite 4B", "908 Harbor View Avenue"],
    )

    city: str = Field(
        default="",
        title="City",
        description="The city",
        examples=["North Briar", "Maple Glen", "Harbor Point"],
    )
    
    province: str = Field(
        default="",
        title="Province",
        description="The province",
        examples=["Westfield", "Lake District", "North County"],
    )

    postalcode: str = Field(
        default="",
        title="Postal code",
        description="The postal code",
        examples=["WL3 8QT", "MC4 2LB", "HV7 1RN"],
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
    ui.form_builder(contact_address)


def main(*, port: int = 8080, host: str | None = None, reload: bool = True):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
