/**
 * ProfielScore Form Submission Handler
 * Netlify Serverless Function
 *
 * Flow:
 * 1. Receive form data (LinkedIn URL, email, name, company)
 * 2. Save to Supabase (profielscore_leads table)
 * 3. Send immediate confirmation email via Resend
 * 4. Add to Lemlist campaign (follow-up sequence)
 * 5. Return success
 */

const https = require('https');

// Environment variables
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://jdistoacicmzdazdaubh.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const LEMLIST_API_KEY = process.env.LEMLIST_API_KEY;
const LEMLIST_CAMPAIGN_ID = process.env.LEMLIST_CAMPAIGN_ID;
const RESEND_API_KEY = process.env.RESEND_API_KEY;

// Parse Supabase hostname from URL
const SUPABASE_HOST = SUPABASE_URL.replace('https://', '').replace('http://', '');

/**
 * Make HTTPS request
 */
function makeRequest(hostname, method, path, headers, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname,
      port: 443,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

/**
 * Validate LinkedIn URL
 */
function validateLinkedInUrl(url) {
  const regex = /linkedin\.com\/(in|pub)\/[a-zA-Z0-9\-_%.]+/;
  return regex.test(url);
}

/**
 * Validate email
 */
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

/**
 * Save to Supabase
 */
async function saveToSupabase(formData) {
  const { linkedin_url, email, voornaam, achternaam, telefoonnummer, bedrijfsnaam } = formData;

  const supabaseRes = await makeRequest(
    SUPABASE_HOST,
    'POST',
    '/rest/v1/profielscore_leads',
    {
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'apikey': SUPABASE_ANON_KEY,
      'Prefer': 'return=minimal'
    },
    {
      linkedin_url,
      email,
      voornaam: voornaam || null,
      achternaam: achternaam || null,
      telefoonnummer: telefoonnummer || null,
      bedrijfsnaam: bedrijfsnaam || null,
      status: 'nieuw',
      source: 'profielscore-landing'
    }
  );

  if (supabaseRes.status === 409) {
    console.warn('⚠️  Duplicate email in Supabase, continuing anyway');
    return;
  }

  if (supabaseRes.status !== 200 && supabaseRes.status !== 201 && supabaseRes.status !== 204) {
    throw new Error(`Supabase error: ${supabaseRes.status} - ${JSON.stringify(supabaseRes.body)}`);
  }

  console.log('✅ Saved to Supabase');
}

/**
 * Add to Lemlist Campaign
 */
/**
 * Add to Lemlist Campaign
 * Returns true if lead was added (or already existed), false on failure
 */
async function addToLemlistCampaign(formData) {
  const { email, voornaam, achternaam, linkedin_url } = formData;

  if (!LEMLIST_CAMPAIGN_ID || !LEMLIST_API_KEY) {
    console.error('🚨 LEMLIST_API_KEY or LEMLIST_CAMPAIGN_ID not configured');
    return false;
  }

  try {
    // Lemlist uses Basic Auth: base64(':apiKey')
    const basicAuth = Buffer.from(`:${LEMLIST_API_KEY}`).toString('base64');

    const lemlistRes = await makeRequest(
      'api.lemlist.com',
      'POST',
      `/api/campaigns/${LEMLIST_CAMPAIGN_ID}/leads/`,
      {
        'Authorization': `Basic ${basicAuth}`
      },
      {
        email,
        firstName: voornaam || '',
        lastName: achternaam || '',
        linkedinUrl: linkedin_url || ''
      }
    );

    if (lemlistRes.status === 409) {
      console.log('ℹ️  Lead already in Lemlist campaign — OK');
      return true;
    }

    if (lemlistRes.status !== 200 && lemlistRes.status !== 201) {
      console.error(`🚨 Lemlist API error: ${lemlistRes.status}`, JSON.stringify(lemlistRes.body));
      return false;
    }

    console.log('✅ Added to Lemlist campaign');
    return true;
  } catch (err) {
    console.error('🚨 Lemlist request failed:', err.message);
    return false;
  }
}

/**
 * Send immediate confirmation email via Resend
 */
async function sendConfirmationEmail(formData) {
  const { email, voornaam } = formData;
  const naam = voornaam ? voornaam : 'daar';

  if (!RESEND_API_KEY) {
    console.warn('⚠️  RESEND_API_KEY missing, skipping confirmation email');
    return;
  }

  const htmlBody = `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a2e;">
      <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 40px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">ProfielScore</h1>
        <p style="color: #a78bfa; margin: 8px 0 0;">LinkedIn Profiel Analyse</p>
      </div>
      <div style="padding: 40px; background: #ffffff;">
        <h2 style="color: #1a1a2e;">Hoi ${naam},</h2>
        <p style="color: #4a5568; line-height: 1.6;">
          Bedankt voor je aanmelding bij ProfielScore! We hebben je LinkedIn-profiel ontvangen en zijn gestart met de analyse.
        </p>
        <div style="background: #f7f3ff; border-left: 4px solid #7c3aed; padding: 20px; border-radius: 8px; margin: 24px 0;">
          <p style="margin: 0; color: #1a1a2e; font-weight: bold;">Wat kun je verwachten?</p>
          <ul style="color: #4a5568; line-height: 2; margin: 12px 0 0;">
            <li>Je persoonlijke ProfielScore (0-100)</li>
            <li>Concrete verbeterpunten voor jouw profiel</li>
            <li>Tips om meer techtalent aan te trekken</li>
          </ul>
        </div>
        <p style="color: #4a5568;">Je rapport ontvang je <strong>binnen 24 uur</strong> op dit e-mailadres.</p>
        <p style="color: #718096; font-size: 14px; margin-top: 40px;">
          Met vriendelijke groet,<br>
          <strong>Wouter Arts</strong><br>
          Recruitin B.V.
        </p>
      </div>
      <div style="background: #f8f8f8; padding: 20px; text-align: center; font-size: 12px; color: #a0aec0;">
        profielscore.nl &mdash; een dienst van Recruitin B.V.
      </div>
    </div>
  `;

  const resendRes = await makeRequest(
    'api.resend.com',
    'POST',
    '/emails',
    {
      'Authorization': `Bearer ${RESEND_API_KEY}`
    },
    {
      from: 'ProfielScore <noreply@kandidatentekort.nl>',
      to: [email],
      subject: 'Je ProfielScore analyse is gestart!',
      html: htmlBody
    }
  );

  if (resendRes.status !== 200 && resendRes.status !== 201) {
    console.warn(`⚠️  Resend error: ${resendRes.status}`, JSON.stringify(resendRes.body));
    return;
  }

  console.log('✅ Confirmation email sent via Resend');
}

/**
 * Fire-and-forget: trigger Render analyse + rapport email
 * Geen await — Netlify function wacht niet op Render response
 */
function triggerRenderAnalysis(formData) {
  const body = JSON.stringify(formData);
  const req = https.request({
    hostname: 'linkedin-profile-optimizer-api.onrender.com',
    port: 443,
    path: '/profielscore-submit',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body)
    },
    timeout: 300000 // 5 min timeout op Render zijde
  }, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => console.log(`📊 Render analyse klaar: ${res.statusCode} - ${data.substring(0, 100)}`))
  });
  req.on('error', (err) => console.warn(`⚠️  Render analyse fout: ${err.message}`));
  req.write(body);
  req.end();
  console.log('🚀 Render analyse getriggerd (async)');
}

/**
 * Validate required environment variables
 * Returns array of missing var names, empty if all OK
 */
function validateEnvVars() {
  const required = {
    SUPABASE_ANON_KEY: SUPABASE_ANON_KEY,
    RESEND_API_KEY: RESEND_API_KEY,
  };
  const warned = {
    LEMLIST_API_KEY: LEMLIST_API_KEY,
    LEMLIST_CAMPAIGN_ID: LEMLIST_CAMPAIGN_ID,
  };

  const missing = Object.entries(required)
    .filter(([, val]) => !val)
    .map(([key]) => key);

  const missingWarned = Object.entries(warned)
    .filter(([, val]) => !val)
    .map(([key]) => key);

  if (missingWarned.length > 0) {
    console.warn(`⚠️  Optional env vars missing (Lemlist disabled): ${missingWarned.join(', ')}`);
  }

  return missing;
}

/**
 * Main handler
 */
exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  // Validate env vars on every cold start
  const missingVars = validateEnvVars();
  if (missingVars.length > 0) {
    console.error(`❌ Missing required env vars: ${missingVars.join(', ')}`);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Server configuration error. Please contact support.' })
    };
  }

  try {
    const formData = JSON.parse(event.body);
    const { linkedin_url, email, voornaam, achternaam, telefoonnummer, bedrijfsnaam } = formData;

    if (!linkedin_url || !email) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing required fields' })
      };
    }

    if (!validateLinkedInUrl(linkedin_url)) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Invalid LinkedIn URL' })
      };
    }

    if (!validateEmail(email)) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Invalid email address' })
      };
    }

    console.log(`📨 Processing submission: ${email}`);

    // Step 1: Save to database
    await saveToSupabase(formData);

    // Step 2: Send immediate confirmation email
    await sendConfirmationEmail(formData);

    // Step 3: Fire-and-forget → Render analyse + rapport email (async, geen wachten)
    triggerRenderAnalysis(formData);

    // Step 4: Add to Lemlist campaign (non-blocking)
    const lemlistResult = await addToLemlistCampaign(formData);
    if (!lemlistResult) {
      console.warn(`⚠️  Lemlist failed for ${email} — lead in Supabase, rapport via Resend OK`);
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: 'Submission received. You will receive an email within 24 hours.'
      })
    };

  } catch (err) {
    console.error('❌ Error:', err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Server error: ' + err.message })
    };
  }
};
