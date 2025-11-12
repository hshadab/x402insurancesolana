use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod x402_attestation {
    use super::*;

    /// Attest a verified fraud claim proof on-chain
    ///
    /// This stores the proof hash and metadata permanently on Solana,
    /// making it publicly auditable without storing the full proof.
    pub fn attest_claim_proof(
        ctx: Context<AttestProof>,
        claim_id: [u8; 32],
        proof_hash: [u8; 32],
        public_inputs: [u64; 4],
        refund_signature: [u8; 64],
    ) -> Result<()> {
        let attestation = &mut ctx.accounts.attestation;

        attestation.claim_id = claim_id;
        attestation.proof_hash = proof_hash;
        attestation.public_inputs = public_inputs;
        attestation.refund_tx_sig = refund_signature;
        attestation.attested_at = Clock::get()?.unix_timestamp;
        attestation.attester = ctx.accounts.authority.key();
        attestation.bump = ctx.bumps.attestation;

        emit!(ProofAttested {
            claim_id,
            proof_hash,
            payout_amount: public_inputs[3],
            attested_at: attestation.attested_at,
        });

        msg!(
            "Proof attested: claim_id={}, payout={} micro-USDC",
            bs58::encode(&claim_id).into_string(),
            public_inputs[3]
        );

        Ok(())
    }

    /// Query an existing proof attestation
    ///
    /// Anyone can call this to verify a claim was legitimately paid
    pub fn query_attestation(
        ctx: Context<QueryAttestation>,
    ) -> Result<ProofAttestation> {
        let attestation = &ctx.accounts.attestation;

        msg!(
            "Attestation found: claim_id={}, proof_hash={}, payout={}",
            bs58::encode(&attestation.claim_id).into_string(),
            bs58::encode(&attestation.proof_hash).into_string(),
            attestation.public_inputs[3]
        );

        Ok(attestation.clone())
    }
}

#[derive(Accounts)]
#[instruction(claim_id: [u8; 32])]
pub struct AttestProof<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + ProofAttestation::INIT_SPACE,
        seeds = [b"attestation", claim_id.as_ref()],
        bump
    )]
    pub attestation: Account<'info, ProofAttestation>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct QueryAttestation<'info> {
    pub attestation: Account<'info, ProofAttestation>,
}

#[account]
#[derive(InitSpace)]
pub struct ProofAttestation {
    /// Unique claim identifier (32 bytes)
    pub claim_id: [u8; 32],

    /// Blake3 hash of the zkEngine proof (32 bytes)
    pub proof_hash: [u8; 32],

    /// Public inputs to the proof verification:
    /// [fraud_detected, http_status, body_length, payout_amount]
    pub public_inputs: [u64; 4],

    /// Solana transaction signature of the USDC refund (64 bytes)
    pub refund_tx_sig: [u8; 64],

    /// Unix timestamp when attestation was created
    pub attested_at: i64,

    /// Public key of the attester (backend wallet)
    pub attester: Pubkey,

    /// PDA bump seed
    pub bump: u8,
}

#[event]
pub struct ProofAttested {
    pub claim_id: [u8; 32],
    pub proof_hash: [u8; 32],
    pub payout_amount: u64,
    pub attested_at: i64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid proof hash")]
    InvalidProofHash,

    #[msg("Invalid public inputs")]
    InvalidPublicInputs,

    #[msg("Attestation already exists")]
    AttestationExists,
}
