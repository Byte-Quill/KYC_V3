// Supabase Edge Function: generate-embedding
//
// Generates a vector embedding for a KYC application's text and stores it in
// the `kyc_kycapplication.embedding` pgvector column for semantic duplicate /
// fraud detection.
//
// Deploy:
//   supabase functions deploy generate-embedding
//
// Invoke (from Django or a DB webhook on application submit):
//   curl -X POST \
//     -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
//     -H "Content-Type: application/json" \
//     -d '{"application_id": "<uuid>"}' \
//     https://<ref>.functions.supabase.co/generate-embedding
//
// Set these secrets first:
//   supabase secrets set OPENAI_API_KEY=... SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...

import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
// Shared secret that Django sends as `Authorization: Bearer <secret>`.
// Set via: supabase secrets set FUNCTION_SECRET=<random>
const FUNCTION_SECRET = Deno.env.get("FUNCTION_SECRET") ?? "";

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  // Fail closed: refuse to run when required config is missing.
  if (!FUNCTION_SECRET || !OPENAI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    return Response.json({ error: "Function is not configured" }, { status: 500 });
  }

  const auth = req.headers.get("Authorization") ?? "";
  if (auth !== `Bearer ${FUNCTION_SECRET}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { application_id } = await req.json();
  if (!application_id) {
    return Response.json({ error: "application_id is required" }, { status: 400 });
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

  // 1. Load the application text.
  const { data: app, error } = await supabase
    .from("kyc_kycapplication")
    .select("id, full_name, nationality, country, id_type, id_number")
    .eq("id", application_id)
    .single();

  if (error || !app) {
    return Response.json({ error: "Application not found" }, { status: 404 });
  }

  const text = [
    app.full_name,
    app.nationality,
    app.country,
    app.id_type,
    app.id_number,
  ].join(" | ");

  // 2. Generate the embedding.
  const embRes = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: "text-embedding-3-small", input: text }),
  });
  const embJson = await embRes.json();
  const embedding = embJson?.data?.[0]?.embedding;
  if (!embedding) {
    return Response.json({ error: "Embedding generation failed" }, { status: 502 });
  }

  // 3. Store it back on the row.
  const { error: updateError } = await supabase
    .from("kyc_kycapplication")
    .update({ embedding })
    .eq("id", application_id);

  if (updateError) {
    return Response.json({ error: updateError.message }, { status: 500 });
  }

  return Response.json({ ok: true, application_id, dimensions: embedding.length });
});
