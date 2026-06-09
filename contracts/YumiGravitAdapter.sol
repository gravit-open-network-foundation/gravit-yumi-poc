// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

/**
 * @title YumiGravitAdapter
 * @notice Adapter between Yumi Finance credit engine and Gravit trust layer
 * @dev This contract allows Yumi to verify credit decisions through Gravit
 */
contract YumiGravitAdapter {

    // ============ Structs ============

    struct VerificationProof {
        bytes32 traceId;
        uint8 trustScore;
        bool allowed;
        bytes signature;
    }

    struct CreditRequest {
        address borrower;
        uint256 amount;
        uint256 termDays;
        bytes32 dataHash;
        uint256 timestamp;
    }

    // ============ State Variables ============

    address public gravitVerifier;
    address public yumiCreditEngine;
    uint8 public constant MIN_TRUST_SCORE = 200; // Out of 255

    mapping(bytes32 => bool) public usedProofs;
    mapping(bytes32 => CreditRequest) public creditRequests;

    // ============ Events ============

    event CreditVerified(
        bytes32 indexed traceId,
        address indexed borrower,
        uint256 amount,
        uint8 trustScore,
        bool approved
    );

    event ProofUsed(bytes32 indexed proofHash, bytes32 indexed traceId);

    // ============ Modifiers ============

    modifier onlyGravit() {
        require(msg.sender == gravitVerifier, "Only Gravit verifier");
        _;
    }

    modifier onlyYumi() {
        require(msg.sender == yumiCreditEngine, "Only Yumi credit engine");
        _;
    }

    // ============ Constructor ============

    constructor(address _gravitVerifier, address _yumiCreditEngine) {
        gravitVerifier = _gravitVerifier;
        yumiCreditEngine = _yumiCreditEngine;
    }

    // ============ Core Functions ============

    /**
     * @notice Submit credit request for verification
     * @param request Credit request data
     * @return proofHash Unique hash of the verification request
     */
    function submitCreditRequest(
        CreditRequest calldata request
    ) external onlyYumi returns (bytes32 proofHash) {
        proofHash = keccak256(abi.encode(request));
        creditRequests[proofHash] = request;
        return proofHash;
    }

    /**
     * @notice Receive verification result from Gravit
     * @param proofHash Hash of the original credit request
     * @param verification Gravit verification result
     */
    function receiveVerification(
        bytes32 proofHash,
        VerificationProof calldata verification
    ) external onlyGravit {
        require(!usedProofs[proofHash], "Proof already used");
        require(creditRequests[proofHash].timestamp > 0, "Unknown credit request");

        usedProofs[proofHash] = true;

        CreditRequest memory request = creditRequests[proofHash];
        bool approved = verification.allowed && verification.trustScore >= MIN_TRUST_SCORE;

        emit CreditVerified(
            verification.traceId,
            request.borrower,
            request.amount,
            verification.trustScore,
            approved
        );

        // Notify Yumi credit engine
        (bool success, ) = yumiCreditEngine.call(
            abi.encodeWithSignature(
                "onVerificationResult(bytes32,address,uint256,bool)",
                verification.traceId,
                request.borrower,
                request.amount,
                approved
            )
        );

        require(success, "Failed to notify credit engine");
    }

    /**
     * @notice Verify a proof off-chain (for frontend integration)
     * @param proof Verification proof
     * @return isValid Whether the proof is valid and not used
     */
    function verifyProof(VerificationProof calldata proof) external view returns (bool isValid) {
        bytes32 proofHash = keccak256(abi.encode(proof));
        return !usedProofs[proofHash];
    }

    /**
     * @notice Get minimum trust score required for approval
     */
    function getMinTrustScore() external view returns (uint8) {
        return MIN_TRUST_SCORE;
    }

    /**
     * @notice Update Gravit verifier address (governance)
     */
    function updateGravitVerifier(address newVerifier) external onlyYumi {
        gravitVerifier = newVerifier;
    }
}
