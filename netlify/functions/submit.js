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

  if (supabaseRes.status !== 200 && supabaseRes.status !== 201 && supabaseRes.status !== 204) {
    throw new Error(`Supabase error: ${supabaseRes.status} - ${JSON.stringify(supabaseRes.body)}`);
  }

  console.log('✅ Saved to Supabase');
}

/**
 * Add to Lemlist Campaign
 */
async function addToLemlistCampaign(formData) {
  const { email, voornaam, achternaam } = formData;

  if (!LEMLIST_CAMPAIGN_ID || !LEMLIST_API_KEY) {
    console.warn('⚠️  LEMLIST config missing, skipping');
    return;
  }

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
      lastName: achternaam || ''
    }
  );

  if (lemlistRes.status === 409) {
    console.warn('⚠️  Lead already in Lemlist campaign');
    return;
  }

  if (lemlistRes.status !== 200 && lemlistRes.status !== 201) {
    console.warn(`⚠️  Lemlist error: ${lemlistRes.status}`, JSON.stringify(lemlistRes.body));
    return;
  }

  console.log('✅ Added to Lemlist campaign');
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
      from: 'Recruitin <noreply@recruitin.nl>',
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
 * Main handler
 */
exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
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

    await saveToSupabase(formData);
    await sendConfirmationEmail(formData);
    await addToLemlistCampaign(formData);

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
