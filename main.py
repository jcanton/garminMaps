#!/usr/bin/env python3

import configparser
import logging
import os
import socket
import sys
from datetime import date, datetime
from getpass import getpass
from pathlib import Path

import requests
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garth.exc import GarthException, GarthHTTPError

import gmFunctions as gmf

# ===============================================================================
# Data and config
#
config = configparser.ConfigParser()
config.read(os.path.join(os.path.expanduser("~"), ".python-github.cfg"))
GARMIN_ID = config.get("garmin.maps", "GARMIN_ID")
GARMIN_PW = config.get("garmin.maps", "GARMIN_PW")
GARMIN_AC = config.get("garmin.maps", "GARMIN_ACTIVITIES")
GARMIN_DS = config.get("garmin.maps", "GARMIN_DATESTART")

activityTypes = GARMIN_AC.strip().replace(" ", "").split(",")
cpDateStart = [int(ymd) for ymd in GARMIN_DS.strip().split("-")]

today = date.today()
dateStart = date(cpDateStart[0], cpDateStart[1], cpDateStart[2])
dateEnd = today

execLog = "log_exec.log"
msgLog = "log_msg.log"
gpxDir = "gpxFiles"
mapDir = "maps"

# ===============================================================================
# Check whether the script already ran today
#
if os.path.isfile(execLog):
    with open(execLog, "r") as filehandle:
        lastRun = datetime.fromisoformat(filehandle.readline())

        if lastRun.date() == today:
            # exit
            print("Already run today")
            sys.exit()

# ===============================================================================
# Initialize logger
#
logging.basicConfig(
    filename=msgLog, level=logging.INFO, format="%(message)s", filemode="w"
)

logging.info("============= start mapping =============")
logging.info("Host: " + socket.gethostname())
logging.info("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M"))

# ===============================================================================
# Init Garmin client and log in
#


def safe_api_call(api_method, *args, **kwargs):
    """
    Safe API call wrapper with comprehensive error handling.

    This demonstrates the error handling patterns used throughout the library.
    Returns (success: bool, result: Any, error_message: str)
    """
    try:
        result = api_method(*args, **kwargs)
        return True, result, None

    except GarthHTTPError as e:
        # Handle specific HTTP errors gracefully
        error_str = str(e)
        status_code = getattr(getattr(e, "response", None), "status_code", None)

        if status_code == 400 or "400" in error_str:
            return (
                False,
                None,
                "Endpoint not available (400 Bad Request) - Feature may not be enabled for your account",
            )
        elif status_code == 401 or "401" in error_str:
            return (
                False,
                None,
                "Authentication required (401 Unauthorized) - Please re-authenticate",
            )
        elif status_code == 403 or "403" in error_str:
            return (
                False,
                None,
                "Access denied (403 Forbidden) - Account may not have permission",
            )
        elif status_code == 404 or "404" in error_str:
            return (
                False,
                None,
                "Endpoint not found (404) - Feature may have been moved or removed",
            )
        elif status_code == 429 or "429" in error_str:
            return (
                False,
                None,
                "Rate limit exceeded (429) - Please wait before making more requests",
            )
        elif status_code == 500 or "500" in error_str:
            return (
                False,
                None,
                "Server error (500) - Garmin's servers are experiencing issues",
            )
        elif status_code == 503 or "503" in error_str:
            return (
                False,
                None,
                "Service unavailable (503) - Garmin's servers are temporarily unavailable",
            )
        else:
            return False, None, f"HTTP error: {e}"

    except FileNotFoundError:
        return (
            False,
            None,
            "No valid tokens found. Please login with your email/password to create new tokens.",
        )

    except GarminConnectAuthenticationError as e:
        return False, None, f"Authentication issue: {e}"

    except GarminConnectConnectionError as e:
        return False, None, f"Connection issue: {e}"

    except GarminConnectTooManyRequestsError as e:
        return False, None, f"Rate limit exceeded: {e}"

    except Exception as e:
        return False, None, f"Unexpected error: {e}"


def get_credentials():
    """Get email and password from environment or user input."""
    # email = os.getenv("EMAIL")
    # password = os.getenv("PASSWORD")

    email = config.get("garmin.maps", "GARMIN_ID")
    password = config.get("garmin.maps", "GARMIN_PW")

    if not email:
        email = input("Login email: ")
    if not password:
        password = getpass("Enter password: ")

    return email, password


def init_api() -> Garmin | None:
    """Initialize Garmin API with authentication and token management."""

    # Configure token storage
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = Path(tokenstore).expanduser()

    print(f"🔐 Token storage: {tokenstore_path}")

    # Check if token files exist
    if tokenstore_path.exists():
        print("📄 Found existing token directory")
        token_files = list(tokenstore_path.glob("*.json"))
        if token_files:
            print(
                f"🔑 Found {len(token_files)} token file(s): {[f.name for f in token_files]}"
            )
        else:
            print("⚠️ Token directory exists but no token files found")
    else:
        print("📭 No existing token directory found")

    # First try to login with stored tokens
    try:
        print("🔄 Attempting to use saved authentication tokens...")
        garmin = Garmin()
        garmin.login(str(tokenstore_path))
        print("✅ Successfully logged in using saved tokens!")
        return garmin

    except (
        FileNotFoundError,
        GarthHTTPError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ):
        print("🔑 No valid tokens found. Requesting fresh login credentials.")

    # Loop for credential entry with retry on auth failure
    while True:
        try:
            # Get credentials
            email, password = get_credentials()

            print("� Logging in with credentials...")
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                print("🔐 Multi-factor authentication required")

                mfa_code = input("Please enter your MFA code: ")
                print("🔄 Submitting MFA code...")

                try:
                    garmin.resume_login(result2, mfa_code)
                    print("✅ MFA authentication successful!")

                except GarthHTTPError as garth_error:
                    # Handle specific HTTP errors from MFA
                    error_str = str(garth_error)
                    if "429" in error_str and "Too Many Requests" in error_str:
                        print("❌ Too many MFA attempts")
                        print("💡 Please wait 30 minutes before trying again")
                        sys.exit(1)
                    elif "401" in error_str or "403" in error_str:
                        print("❌ Invalid MFA code")
                        print("💡 Please verify your MFA code and try again")
                        continue
                    else:
                        # Other HTTP errors - don't retry
                        print(f"❌ MFA authentication failed: {garth_error}")
                        sys.exit(1)

                except GarthException as garth_error:
                    print(f"❌ MFA authentication failed: {garth_error}")
                    print("💡 Please verify your MFA code and try again")
                    continue

            # Save tokens for future use
            garmin.garth.dump(str(tokenstore_path))
            print(f"💾 Authentication tokens saved to: {tokenstore_path}")
            print("✅ Login successful!")
            return garmin

        except GarminConnectAuthenticationError:
            print("❌ Authentication failed:")
            print("💡 Please check your username and password and try again")
            # Continue the loop to retry
            continue

        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectConnectionError,
            requests.exceptions.HTTPError,
        ) as err:
            print(f"❌ Connection error: {err}")
            print("💡 Please check your internet connection and try again")
            return None

        except KeyboardInterrupt:
            print("\n👋 Cancelled by user")
            return None


def display_user_info(api: Garmin):
    """Display basic user information with proper error handling."""
    print("\n" + "=" * 60)
    print("👤 User Information")
    print("=" * 60)

    # Get user's full name
    success, full_name, error_msg = safe_api_call(api.get_full_name)
    if success:
        print(f"📝 Name: {full_name}")
    else:
        print(f"📝 Name: ⚠️ {error_msg}")

    # Get user profile number from device info
    success, device_info, error_msg = safe_api_call(api.get_device_last_used)
    if success and device_info and device_info.get("userProfileNumber"):
        user_profile_number = device_info.get("userProfileNumber")
        print(f"🆔 Profile Number: {user_profile_number}")
    else:
        if not success:
            print(f"🆔 Profile Number: ⚠️ {error_msg}")
        else:
            print("🆔 Profile Number: Not available")


try:
    # Initialize API with authentication (will only prompt for credentials if needed)
    api = init_api()

    if not api:
        print("❌ Failed to initialize API. Exiting.")
        sys.exit(1)

    # Display user information
    display_user_info(api)

except (
    GarminConnectConnectionError,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
) as err:
    logging.info("Error occurred during Garmin Connect Client login: %s" % err)
    sys.exit()
except Exception:  # pylint: disable=broad-except
    logging.info("Unknown error occurred during Garmin Connect Client login")
    sys.exit()
fullName = api.get_full_name()
unitSystem = api.get_unit_system()

logging.info("Garmin user: " + fullName)
logging.info("Unit system: " + unitSystem)

# ===============================================================================
# Save activities to gpx files
#
#doneAct = gmf.activitiesToGpx(dateStart, dateEnd, api, activityTypes, gpxDir, logging)

# ===============================================================================
# Build maps
#
doneMap = gmf.buildMaps(activityTypes, gpxDir, mapDir, logging)

# ===============================================================================
# Update last exec file
#
if (doneAct == 0) and (doneMap == 0):
    # the script ran succesfully
    with open(execLog, "w") as filehandle:
        filehandle.write(datetime.now().isoformat())
