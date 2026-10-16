import factory

from apps.accounts.models import Role, User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = Role.CUSTOMER

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "StrongPass9!")
        if create:
            self.save()
