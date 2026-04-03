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
    const { linkedin_url, email, voornaam, achternaam, telefoonnummer, doel, source } = JSON.parse(event.body);

    // Validation
    if (!linkedin_url || !email || !doel) {
      return {
        statusCode: 400,
        headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'LinkedIn URL, email en doel zijn verplicht' })
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

    // 1. Insert to Supabase
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

    if (!supabaseUrl || !supabaseKey) {
      console.error('Supabase credentials not configured');
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'Server configuration error' })
      };
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    await supabase.from('profielscore_leads').upsert(
      {
        linkedin_url,
        email,
        voornaam: voornaam || null,
        achternaam: achternaam || null,
        telefoonnummer: telefoonnummer || null,
        doel,
        status: 'nieuw',
        source: source || 'profielscore-landing',
        created_at: new Date().toISOString()
      },
      { onConflict: 'email' }
    );

    // 2. Add to Lemlist
    const lemlistApiKey = process.env.LEMLIST_API_KEY;
    if (!lemlistApiKey) {
      console.warn('LEMLIST_API_KEY not configured - skipping Lemlist');
    } else {
      try {
        const lemlistRes = await fetch(
          'https://api.lemlist.com/api/campaigns/cam_profielscore/leads',
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${lemlistApiKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              email,
              firstName: voornaam || '',
              lastName: achternaam || '',
              phone: telefoonnummer || '',
              customFields: {
                doel: doel
              }
            })
          }
        );

        if (!lemlistRes.ok) {
          const error = await lemlistRes.json();
          console.error('Lemlist error:', error);
        }
      } catch (lemlistErr) {
        console.error('Lemlist connection error:', lemlistErr);
        // Don't fail the whole request if Lemlist fails
      }
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: 'Aanvraag ontvangen. Rapport volgt binnen 24 uur.'
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
