/**
 * ProfielScore Form Submission Handler
 * Netlify Serverless Function
 *
 * Flow:
 * 1. Receive form data (LinkedIn URL, email, name, goal)
 * 2. Save to Supabase (profielscore_leads table)
 * 3. Add to Lemlist campaign
 * 4. Return success
 */

const https = require('https');

// Environment variables
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://jdistoacicmzdazdaubh.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const LEMLIST_API_KEY = process.env.LEMLIST_API_KEY;
const LEMLIST_CAMPAIGN_ID = process.env.LEMLIST_CAMPAIGN_ID;

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
  const { linkedin_url, email, voornaam, achternaam, telefoonnummer, doel } = formData;

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
      status: 'nieuw',
      source: doel ? `profielscore-${doel}` : 'profielscore-landing'
    }
  );

  if (supabaseRes.status !== 200 && supabaseRes.status !== 201) {
    throw new Error(`Supabase error: ${supabaseRes.status} - ${JSON.stringify(supabaseRes.body)}`);
  }

  console.log('✅ Saved to Supabase');
}

/**
 * Add to Lemlist Campaign
 */
async function addToLemlistCampaign(formData) {
  const { email, voornaam } = formData;

  if (!LEMLIST_CAMPAIGN_ID) {
    console.warn('⚠️  LEMLIST_CAMPAIGN_ID not set, skipping Lemlist');
    return;
  }

  const lemlistRes = await makeRequest(
    'api.lemlist.com',
    'POST',
    `/v1/campaigns/${LEMLIST_CAMPAIGN_ID}/leads`,
    {
      'X-API-Key': LEMLIST_API_KEY
    },
    {
      email,
      firstName: voornaam || ''
    }
  );

  if (lemlistRes.status === 400 && lemlistRes.body.error?.includes('already')) {
    console.warn('⚠️  Lead already in campaign');
    return;
  }

  if (lemlistRes.status !== 200 && lemlistRes.status !== 201) {
    console.warn(`⚠️  Lemlist error: ${lemlistRes.status}`, lemlistRes.body);
    return;
  }

  console.log('✅ Added to Lemlist campaign');
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
    const { linkedin_url, email, voornaam, achternaam, telefoonnummer, doel } = formData;

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
