# Salesforce Connected App Setup Guide

To use this DocAI Mini application, you need to set up a **Connected App** in your Salesforce org. This app handles the OAuth authentication allowing the application to access Salesforce Data Cloud services on your behalf.

## Prerequisites

*   A Salesforce Org with **Data Cloud** enabled.
*   **Intelligent Document Processing** (IDP) enabled in Data Cloud Setup.

## Step 1: Create a Connected App

1.  Log in to your Salesforce Org.
2.  Go to **Setup**.
3.  In the Quick Find box, search for **App Manager**.
4.  Click **New Connected App** (top right).

## Step 2: Configure Basic Information

*   **Connected App Name**: `DocAI Mini` (or any name you prefer)
*   **API Name**: `DocAI_Mini`
*   **Contact Email**: Your email address.

## Step 3: Enable OAuth Settings

1.  Check the box **Enable OAuth Settings**.
2.  **Callback URL**:
    *   **For Local Development**: `http://localhost:5002/auth/callback` (Note: Port 5002 is used in this setup)
    *   **For Vercel Deployment**: `https://<your-vercel-project-name>.vercel.app/auth/callback`
    *   *Tip: You can add multiple callback URLs on separate lines.*
3.  **Selected OAuth Scopes**:
    *   Add the following scopes:
        *   `Manage user data via APIs (api)`
        *   `Perform requests on your behalf at any time (refresh_token, offline_access)`
        *   `Full access (full)` (Optional, but ensures all permissions)
4.  **Require Secret for Web Server Flow**: Ensure this is **checked**.
5.  **Require Proof Key for Code Exchange (PKCE) Extension for Supported Authorization Flows**: Uncheck this for now unless you want to implement PKCE on the frontend (this app uses standard Authorization Code flow).
6.  Click **Save**.
7.  Click **Continue**.

## Step 4: Manage Consumer Details

1.  On the Connected App page, locate the **Consumer Key and Secret** section.
2.  Click **Manage Consumer Details**.
3.  Verify your identity if prompted.
4.  Copy the **Consumer Key** (Client ID) and **Consumer Secret** (Client Secret).
    *   You will need these when configuring the DocAI Mini app.

## Step 5: Configure OAuth Policies (Important)

1.  Go back to **App Manager**.
2.  Find your app (`DocAI Mini`), click the dropdown arrow, and select **Manage**.
3.  Click **Edit Policies**.
4.  **IP Relaxation**: Change to `Relax IP restrictions` (recommended for development/testing).
5.  **Permitted Users**: Ensure it is set to `All users may self-authorize`.
6.  Click **Save**.

## Step 6: Enable Document AI (Data Cloud)

1.  In Salesforce Setup, search for **Intelligent Document Processing**.
2.  Ensure it is **Enabled**.
3.  (Optional) Setup a specific **IDP Configuration** if you want to use predefined extraction rules.

## Using the App

1.  Open the DocAI Mini app.
2.  Paste your **Login URL** (e.g., `login.salesforce.com`), **Client ID**, and **Client Secret**.
3.  Click **Login to Salesforce**.
4.  Allow access when prompted.

