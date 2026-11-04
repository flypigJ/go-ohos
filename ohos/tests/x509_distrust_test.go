// K1-only regression, supplied to crypto/x509 through a Go test overlay.
// This file is never part of the application or the distributed toolchain.
package x509

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509/pkix"
	"encoding/hex"
	"errors"
	"math/big"
	"testing"
	"time"
)

func TestMeshArcDistrustCatalogue(t *testing.T) {
	// Pin the official Go 1.27.3 public-key distrust list independently of the
	// port. Porting must not remove or substitute the security update.
	want := []string{
		"ebed6475c2c2d80fcb199f3fe8dd6e6b3ce60b77eb15d4e42c3dec0c6f5b5105",
		"49dd353dc2b919a3770645117d0e60c16115e7d1bc259eefe734b00ea434fe5f",
		"e0254c7fcdc265e2f0f8a428dabb75ab4ae039b4872d62f5ee57f0877d5a8a41",
		"5c0660a2b164910d8ff589c18e14552e9e0ec237dcefe2cb736d41a4811f81a0",
		"43bffa19d6ef651451f6841e019931e96f6f2eaeff28ab4b6f1ce4576de2717b",
		"63ecefee431d49523bc1136c4e72d0206a477086caf606cd5cf025686c109cf8",
		"ec4ffa1ad0ac88081314b7aaffef6a91f97cd57291bb5ba686c5415f5eb4f6b6",
		"92c063d67e8f14db71d288e11266ffdaf69cbf115f7bab14f3bc2f68d25e0e30",
	}
	if len(distrustedSPKIHashes) != len(want) {
		t.Fatalf("unexpected official distrust list length: %d", len(distrustedSPKIHashes))
	}
	for _, hash := range want {
		if _, ok := distrustedSPKIHashes[hash]; !ok {
			t.Fatalf("official distrust entry missing: %s", hash)
		}
	}
}

func TestMeshArcDistrustVerify(t *testing.T) {
	// Build an otherwise valid, private test chain; no system trust store is
	// changed. Inject its SPKI digest only into this isolated test process to
	// exercise the real Verify path, including ExtKeyUsageAny.
	now := time.Unix(1700000000, 0)
	issue := func(serial int64, ca bool, parent *Certificate, signer *ecdsa.PrivateKey) (*Certificate, *ecdsa.PrivateKey) {
		t.Helper()
		key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
		if err != nil {
			t.Fatal(err)
		}
		template := &Certificate{
			SerialNumber: big.NewInt(serial), Subject: pkix.Name{CommonName: "MeshArc K1 local test"},
			NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour),
			BasicConstraintsValid: true, IsCA: ca, KeyUsage: KeyUsageDigitalSignature,
			DNSNames: []string{"mesharc-k1.test"}, ExtKeyUsage: []ExtKeyUsage{ExtKeyUsageServerAuth},
		}
		if ca {
			template.KeyUsage |= KeyUsageCertSign
		}
		if parent == nil {
			parent, signer = template, key
		}
		der, err := CreateCertificate(rand.Reader, template, parent, &key.PublicKey, signer)
		if err != nil {
			t.Fatal(err)
		}
		cert, err := ParseCertificate(der)
		if err != nil {
			t.Fatal(err)
		}
		return cert, key
	}
	root, rootKey := issue(1, true, nil, nil)
	intermediate, intermediateKey := issue(2, true, root, rootKey)
	leaf, _ := issue(3, false, intermediate, intermediateKey)
	roots, intermediates := NewCertPool(), NewCertPool()
	roots.AddCert(root)
	intermediates.AddCert(intermediate)
	opts := VerifyOptions{Roots: roots, Intermediates: intermediates, DNSName: "mesharc-k1.test", CurrentTime: now}
	checkValid := func() {
		t.Helper()
		chains, err := leaf.Verify(opts)
		if err != nil || len(chains) != 1 || len(chains[0]) != 3 {
			t.Fatalf("control chain must verify: chains=%d err=%v", len(chains), err)
		}
	}
	checkValid()
	for _, item := range []struct {
		name string
		cert *Certificate
	}{{"leaf", leaf}, {"intermediate", intermediate}, {"root", root}} {
		t.Run(item.name, func(t *testing.T) {
			hash := sha256.Sum256(item.cert.RawSubjectPublicKeyInfo)
			key := hex.EncodeToString(hash[:])
			distrustedSPKIHashes[key] = struct{}{}
			t.Cleanup(func() { delete(distrustedSPKIHashes, key) })
			for _, usage := range []ExtKeyUsage{ExtKeyUsageServerAuth, ExtKeyUsageAny} {
				opts.KeyUsages = []ExtKeyUsage{usage}
				chains, err := leaf.Verify(opts)
				var invalid CertificateInvalidError
				if len(chains) != 0 || !errors.As(err, &invalid) || invalid.Reason != NoValidChains {
					t.Fatalf("distrusted chain was not rejected: usage=%v chains=%d err=%v", usage, len(chains), err)
				}
			}
		})
		checkValid()
	}
}
