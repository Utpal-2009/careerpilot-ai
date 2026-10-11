
"""PIN-protected demo access for CareerPilot AI."""

from datetime import date
import hmac

import streamlit as st


MAX_ATTEMPTS = 5


def verify_demo_access() -> bool:
    """Display the demo login screen and verify the configured PIN."""

    # Initialize session state
    if "demo_access_granted" not in st.session_state:
        st.session_state.demo_access_granted = False

    if "demo_pin_attempts" not in st.session_state:
        st.session_state.demo_pin_attempts = 0

    # Already authenticated in this session
    if st.session_state.demo_access_granted:
        return True

    # Read configuration
    try:
        configured_pin = str(st.secrets["DEMO_ACCESS_PIN"])
        expiry_date = date.fromisoformat(
            str(st.secrets["DEMO_EXPIRY_DATE"])
        )
    except Exception:
        st.error(
            "Demo access is not configured correctly. "
            "Check .streamlit/secrets.toml."
        )
        st.stop()

    # Validate PIN configuration
    if len(configured_pin) != 4 or not configured_pin.isdigit():
        st.error("DEMO_ACCESS_PIN must contain exactly 4 digits.")
        st.stop()

    # Expiry validation
    if date.today() > expiry_date:
        st.markdown(
            """
            <style>
            .block-container {
                max-width: 500px;
                padding-top: 12vh;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.title("🔒 CareerPilot AI")
        st.error("This demo access period has expired.")
        st.info("Please contact the developer for updated access.")
        st.stop()

    # Premium, uncluttered login styling
    st.markdown(
        """
        <style>
        /* Hide unnecessary Streamlit elements */
        #MainMenu,
        footer {
            visibility: hidden;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        /* Center the complete login screen */
        .block-container {
            max-width: 480px !important;
            padding: 7vh 16px 24px 16px !important;
        }

        /* Single card heading */
        .demo-card {
            box-sizing: border-box;
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            padding: 30px 26px 22px;
            background: #151b2b;
            border: 1px solid #30394d;
            border-bottom: none;
            border-radius: 18px 18px 0 0;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.22);
            text-align: center;
        }

        .demo-icon {
            font-size: 36px;
            line-height: 1.4;
            margin-bottom: 10px;
        }

        .demo-title {
            color: #ffffff;
            font-size: 25px;
            font-weight: 750;
            letter-spacing: -0.5px;
            margin-bottom: 12px;
        }

        .demo-description {
            color: #b9c3d6;
            font-size: 14px;
            line-height: 1.65;
            margin: 0;
        }

        /* Form visually joins the heading card */
        div[data-testid="stForm"] {
            box-sizing: border-box;
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            padding: 8px 26px 26px;
            background: #151b2b;
            border: 1px solid #30394d;
            border-top: none;
            border-radius: 0 0 18px 18px;
        }

        /* Label */
        div[data-testid="stForm"] label {
            color: #dce3ef;
            font-size: 13px;
            font-weight: 600;
        }

        /* PIN input */
        div[data-testid="stForm"] input {
            box-sizing: border-box;
            min-height: 48px;
            text-align: center;
            letter-spacing: 8px;
            font-size: 20px;
            border-radius: 10px;
        }

        /* Submit button */
        div[data-testid="stFormSubmitButton"] button {
            width: 100%;
            min-height: 46px;
            margin-top: 12px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 650;
        }

        div[data-testid="stFormSubmitButton"] button:hover {
            filter: brightness(1.06);
        }

        /* Footer */
        .demo-footer {
            max-width: 420px;
            margin: 18px auto 0;
            color: #8994a9;
            text-align: center;
            font-size: 12px;
        }

        /* Mobile layout */
        @media (max-width: 600px) {
            .block-container {
                padding: 5vh 12px 20px !important;
            }

            .demo-card {
                padding: 26px 18px 20px;
            }

            div[data-testid="stForm"] {
                padding: 8px 18px 22px;
            }

            .demo-title {
                font-size: 23px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Card heading
    st.markdown(
        """
        <div class="demo-card">
            <div class="demo-icon">🔐</div>
            <div class="demo-title">Private Demo Access</div>
            <p class="demo-description">
                Enter the access code provided by the developer
                to explore CareerPilot AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Limit incorrect attempts in the current session
    if st.session_state.demo_pin_attempts >= MAX_ATTEMPTS:
        st.error(
            "Maximum incorrect attempts reached. "
            "Please contact the developer."
        )
        st.stop()

    # PIN form
    with st.form("demo_access_form"):
        pin = st.text_input(
            "Enter 4-digit access code",
            type="password",
            max_chars=4,
            placeholder="••••",
            help="Enter the four-digit code provided by the developer.",
        )

        submitted = st.form_submit_button(
            "Verify Access",
            type="primary",
            use_container_width=True,
        )

    # Verify submitted PIN
    if submitted:
        valid_pin = (
            len(pin) == 4
            and pin.isdigit()
            and hmac.compare_digest(pin, configured_pin)
        )

        if valid_pin:
            st.session_state.demo_access_granted = True
            st.rerun()
        else:
            st.session_state.demo_pin_attempts += 1
            remaining = MAX_ATTEMPTS - st.session_state.demo_pin_attempts

            if remaining > 0:
                st.error(
                    f"Incorrect access code. "
                    f"{remaining} attempt(s) remaining."
                )
            else:
                st.error(
                    "Maximum attempts reached. "
                    "Please contact the developer."
                )

    # Footer
    st.markdown(
        """
        <div class="demo-footer">
            🔒 Authorized demonstration only
        </div>
        """,
        unsafe_allow_html=True,
    )

    return False
