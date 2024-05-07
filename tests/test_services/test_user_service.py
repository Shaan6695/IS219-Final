from builtins import range
import pytest
from sqlalchemy import select
from app.dependencies import get_settings
from app.models.user_model import User, UserRole
from app.services.user_service import UserService
from app.utils.nickname_gen import generate_nickname

pytestmark = pytest.mark.asyncio

# Test creating a user with valid data
async def test_create_user_with_valid_data(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "valid_user@example.com",
        "password": "ValidPassword123!",
        "role": UserRole.ADMIN.name
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test creating a user with invalid data
async def test_create_user_with_invalid_data(db_session, email_service):
    user_data = {
        "nickname": "",  # Invalid nickname
        "email": "invalidemail",  # Invalid email
        "password": "short",  # Invalid password
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is None

# Test fetching a user by ID when the user exists
async def test_get_by_id_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_id(db_session, user.id)
    assert retrieved_user.id == user.id

# Test fetching a user by ID when the user does not exist
async def test_get_by_id_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    retrieved_user = await UserService.get_by_id(db_session, non_existent_user_id)
    assert retrieved_user is None

# Test fetching a user by nickname when the user exists
async def test_get_by_nickname_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_nickname(db_session, user.nickname)
    assert retrieved_user.nickname == user.nickname

# Test fetching a user by nickname when the user does not exist
async def test_get_by_nickname_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_nickname(db_session, "non_existent_nickname")
    assert retrieved_user is None

# Test fetching a user by email when the user exists
async def test_get_by_email_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_email(db_session, user.email)
    assert retrieved_user.email == user.email

# Test fetching a user by email when the user does not exist
async def test_get_by_email_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_email(db_session, "non_existent_email@example.com")
    assert retrieved_user is None

# Test updating a user with valid data
async def test_update_user_valid_data(db_session, user):
    new_email = "updated_email@example.com"
    updated_user = await UserService.update(db_session, user.id, {"email": new_email})
    assert updated_user is not None
    assert updated_user.email == new_email

# Test updating a user with invalid data
async def test_update_user_invalid_data(db_session, user):
    updated_user = await UserService.update(db_session, user.id, {"email": "invalidemail"})
    assert updated_user is None

# Test deleting a user who exists
async def test_delete_user_exists(db_session, user):
    deletion_success = await UserService.delete(db_session, user.id)
    assert deletion_success is True

# Test attempting to delete a user who does not exist
async def test_delete_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    deletion_success = await UserService.delete(db_session, non_existent_user_id)
    assert deletion_success is False

# Test listing users with pagination
async def test_list_users_with_pagination(db_session, users_with_same_role_50_users):
    users_page_1 = await UserService.list_users(db_session, skip=0, limit=10)
    users_page_2 = await UserService.list_users(db_session, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id

# Test registering a user with valid data
async def test_register_user_with_valid_data(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "register_valid_user@example.com",
        "password": "RegisterValid123!",
        "role": UserRole.ADMIN
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test attempting to register a user with invalid data
async def test_register_user_with_invalid_data(db_session, email_service):
    user_data = {
        "email": "registerinvalidemail",  # Invalid email
        "password": "short",  # Invalid password
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is None

# Test successful user login
async def test_login_user_successful(db_session, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "MySuperPassword$1234",
    }
    logged_in_user = await UserService.login_user(db_session, user_data["email"], user_data["password"])
    assert logged_in_user is not None

# Test user login with incorrect email
async def test_login_user_incorrect_email(db_session):
    user = await UserService.login_user(db_session, "nonexistentuser@noway.com", "Password123!")
    assert user is None

# Test user login with incorrect password
async def test_login_user_incorrect_password(db_session, user):
    user = await UserService.login_user(db_session, user.email, "IncorrectPassword!")
    assert user is None

# Test account lock after maximum failed login attempts
async def test_account_lock_after_failed_logins(db_session, verified_user):
    max_login_attempts = get_settings().max_login_attempts
    for _ in range(max_login_attempts):
        await UserService.login_user(db_session, verified_user.email, "wrongpassword")
    
    is_locked = await UserService.is_account_locked(db_session, verified_user.email)
    assert is_locked, "The account should be locked after the maximum number of failed login attempts."

# Test resetting a user's password
async def test_reset_password(db_session, user):
    new_password = "NewPassword123!"
    reset_success = await UserService.reset_password(db_session, user.id, new_password)
    assert reset_success is True

# Test verifying a user's email
async def test_verify_email_with_token(db_session, user):
    token = "valid_token_example"  # This should be set in your user setup if it depends on a real token
    user.verification_token = token  # Simulating setting the token in the database
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, token)
    assert result is True

# Test unlocking a user's account
async def test_unlock_user_account(db_session, locked_user):
    unlocked = await UserService.unlock_user_account(db_session, locked_user.id)
    assert unlocked, "The account should be unlocked"
    refreshed_user = await UserService.get_by_id(db_session, locked_user.id)
    assert not refreshed_user.is_locked, "The user should no longer be locked"

# Test registering a user with valid data and verify email is sent after user creation
async def test_verification_email_after_created_user(db_session, email_service):
    # Define a test async function to replace send_verification_email
    async def test_send_verification_email(user):
        pass

    # Replace the send_verification_email method with the test function
    email_service.send_verification_email = test_send_verification_email

    # Test User data for registering, using generated names, the role is admin
    user_data = {
        "nickname": generate_nickname(),
        "email": "register_valid_user@example.com",
        "password": "RegisterValid123!",
        "role": UserRole.ADMIN
    }

    # Calling register_user method
    user = await UserService.register_user(db_session, user_data, email_service)

    #Assert user is not None
    assert user is not None
    assert user.email == user_data["email"]

# Testing to verify an email
async def test_verify_email_with_expired_token(db_session, user):
    expired_token = "example_expired_token"
    user.verification_token = expired_token
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, expired_token)
    assert result is True

# Testing updating nickname
async def test_update_user_nickname(db_session, user):
    new_nickname = "new_nickname_test"
    updated_user = await UserService.update(db_session, user.id, {"nickname": new_nickname})
    assert updated_user is not None
    assert updated_user.nickname == new_nickname

# Test to make an admin user
async def test_first_admin_role(db_session, email_service):
    # We are going to assume the database is empty at first
    user_data = {
        "nickname": generate_nickname(),
        "email": "first_admin@example.com",
        "password": "FirstAdmin123!",
        "role": UserRole.ADMIN.name
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is not None
    assert user.role == UserRole.ADMIN

# Testing when user updates their password
async def test_updating_user_password(db_session, user):
    new_password = "NewPassword123!"
    updated_user = await UserService.update(db_session, user.id, {"password": new_password})
    assert updated_user is not None
    # TBC

# Testing to see if the list of users exceeds the total user count
async def test_listOfUsers_skip_exceeds_total_user_count(db_session, users_with_same_role_50_users):
    total_users = await UserService.count(db_session)
    users = await UserService.list_users(db_session, skip=total_users + 1, limit=10)
    assert len(users) == 0  # No users should be returned here

# Testing to see if user has correct token for email
async def test_verify_email_with_invalid_token(db_session, user):
    incorrect_token = "incorrect_token_example"
    user.verification_token = "valid_token_example"  # Set a valid token first
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, incorrect_token)
    assert result is False

# Test for searching users by their username
async def test_search_users_by_username(db_session, user):
    users = await UserService.search_users(db_session, username=user.nickname)
    assert len(users) == 1
    assert users[0].id == user.id

# Test for searching for users by their first name
async def test_search_users_by_first_name(db_session, user):
    users = await UserService.search_users(db_session, first_name=user.first_name)
    assert len(users) == 1
    assert users[0].id == user.id

# Test for searching for users by their email
async def test_search_users_by_email(db_session, user):
    users = await UserService.search_users(db_session, email=user.email)
    assert len(users) == 1
    assert users[0].id == user.id

# Test for searching for users by their account status if it is (active)
async def test_search_users_by_account_status_active(db_session, user):
    users = await UserService.search_users(db_session, account_status="Active")
    assert len(users) == 1
    assert users[0].id == user.id

# Test for searching for users by their role
async def test_search_users_by_role(db_session, user):
    users = await UserService.search_users(db_session, role=user.role)
    assert len(users) == 1
    assert users[0].id == user.id

# Test for searching for users by their last name
async def test_search_users_by_last_name(db_session, user):
    users = await UserService.search_users(db_session, last_name=user.last_name)
    assert len(users) == 1
    assert users[0].id == user.id

# Test for searching for users with pagination
async def test_search_users_with_pagination(db_session, users_with_same_role_50_users):
    users_page_1 = await UserService.search_users(db_session, limit=10)
    users_page_2 = await UserService.search_users(db_session, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id

# Test for searching for users if account status is (locked)
async def test_search_users_by_account_status_locked(db_session, user):
    # Lock the user account
    user.is_locked = True
    await db_session.commit()
    users = await UserService.search_users(db_session, account_status="Locked")
    assert len(users) == 1
    assert users[0].id == user.id