import asyncio
import random
import string

from src.infrastructure.database import AsyncSessionFactory
from src.persistence import RoleRepository, UserRepository


async def main():
    async with AsyncSessionFactory() as session:
        roles = await RoleRepository(session).get_all()
        role_ids = [role.id for role in roles]
        data = []
        for _ in range(100):
            name = generate_username()
            d = {
                "role_id": random.choice(role_ids),
                "username": name,
                "email": f"{name}@sentinel.my",
            }
            data.append(d)

        await UserRepository(session).create_bulk(data)


def generate_username():
    # Create a random word from letters
    word = "".join(random.choices(string.ascii_lowercase, k=5))

    # Generate a random number
    number = random.randint(100, 999)

    # Combine the word and the number
    username = word + str(number)

    return username


if __name__ == "__main__":
    asyncio.run(main())
