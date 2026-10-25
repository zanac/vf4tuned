// naomigd_des - decrypt/encrypt a NAOMI GD-ROM game file (e.g. BHX.BIN) with the PIC key.
// Uses the exact DES routine from Flycast (see naomi_des.h).
// Usage: naomigd_des dec|enc <pic-file|16-hex-key> <in> <out>
#include "naomi_des.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static bool key_from_pic(const char *path, u64 &key, char *name)
{
	FILE *f = fopen(path, "rb");
	if (!f) return false;
	std::vector<u8> p(0x4000);
	size_t n = fread(p.data(), 1, p.size(), f);
	fclose(f);
	if (n < 0x4000) return false;
	key = 0;
	for (int i = 0; i < 7; i++) key |= u64(p[0x780 + i * 2]) << (56 - i * 8);
	key |= p[0x7a0];
	for (int i = 0; i < 7; i++) name[i] = p[0x7c0 + i * 2];
	for (int i = 0; i < 7; i++) name[i + 7] = p[0x7e0 + i * 2];
	name[14] = 0;
	return true;
}

int main(int argc, char **argv)
{
	if (argc != 5 || (strcmp(argv[1], "dec") && strcmp(argv[1], "enc"))) {
		fprintf(stderr, "usage: %s dec|enc <pic-file|16-hex-key> <in> <out>\n", argv[0]);
		return 2;
	}
	bool dec = !strcmp(argv[1], "dec");
	u64 key; char name[16] = "";
	if (strlen(argv[2]) == 16 && strspn(argv[2], "0123456789abcdefABCDEF") == 16)
		key = strtoull(argv[2], nullptr, 16);
	else if (!key_from_pic(argv[2], key, name)) {
		fprintf(stderr, "cannot read PIC %s\n", argv[2]);
		return 1;
	}
	fprintf(stderr, "key %016llx%s%s\n", (unsigned long long)key, name[0] ? " file " : "", name);
	u32 sk[32];
	des_generate_subkeys(rev64(key), sk);

	FILE *in = fopen(argv[3], "rb"), *out = fopen(argv[4], "wb");
	if (!in || !out) { fprintf(stderr, "cannot open files\n"); return 1; }
	std::vector<u8> buf(1 << 20);
	size_t n;
	while ((n = fread(buf.data(), 1, buf.size(), in)) > 0) {
		size_t r = (n + 7) & ~size_t(7);
		if (r != n) memset(buf.data() + n, 0, r - n);
		u64 *q = (u64 *)buf.data();
		for (size_t i = 0; i < r / 8; i++)
			q[i] = dec ? des_encrypt_decrypt<true>(q[i], sk) : des_encrypt_decrypt<false>(q[i], sk);
		fwrite(buf.data(), 1, n, out);
	}
	fclose(in); fclose(out);
	return 0;
}
