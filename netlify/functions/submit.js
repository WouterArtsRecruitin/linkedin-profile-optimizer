const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event, context) => {
  // Only accept POST
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type'
      },
      body: ''
    };
  }

  try {
    const { linkedin_url, email } = JSON.parse(event.body);

    // Validation
    if (!linkedin_url || !email) {
      return {
        statusCode: 400,
        headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'LinkedIn URL en email zijn verplicht' })
      };
    }

    // LinkedIn URL validation regex
    const linkedinRegex = /linkedin\.com\/(in|pub)\/[a-zA-Z0-9\-_%.]+/;
    if (!linkedinRegex.test(linkedin_url)) {
      return {
        statusCode: 400,
        headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Ongeldige LinkedIn URL' })
      };
    }

    // Email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return {
        statusCode: 400,
        headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Ongeldig email adres' })
      };
    }

    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json'
    };

    // 1. Submit to Jotform (server-side, API key hidden)
    const jotformApiKey = process.env.JOTFORM_API_TOKEN || process.env.JOTFORM_API_KEY;
    if (!jotformApiKey) {
      console.error('JOTFORM_API_TOKEN environment variable not set');
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'Server configuration error' })
      };
    }

    const jotformRes = await fetch(
      'https://eu-api.jotform.com/form/260606272965058/submissions',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          'submission[46]': linkedin_url,
          'submission[3]': email,
          'apiKey': jotformApiKey
        })
      }
    );

    // 2. Insert to Supabase
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

    if (!supabaseUrl || !supabaseKey) {
      console.error('Supabase credentials not configured');
      // Continue even if Supabase fails - Jotform submission is the main goal
    } else {
      const supabase = createClient(supabaseUrl, supabaseKey);

      await supabase.from('profielscore_leads').upsert(
        {
          linkedin_url,
          email,
          status: 'nieuw',
          source: 'profielscore-landing'
        },
        { onConflict: 'email' }
      );
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: 'Aanvraag ontvangen. Rapport volgt binnen 24 uur.',
        jotform_status: jotformRes.status
      })
    };
  } catch (err) {
    console.error('Form submission error:', err);
    return {
      statusCode: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ error: 'Er ging iets mis. Probeer het opnieuw.' })
    };
  }
};
