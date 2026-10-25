/* cdecc - regenerate Mode 1 EDC/ECC (ECMA-130) for 2352-byte sectors in a raw track file.
 *
 *   cdecc <track.bin> [first_sector count]     fix sectors in place (default: whole file)
 *   cdecc --check <track.bin>                  report sectors whose EDC/ECC would change
 *
 * Only Mode 1 sectors (header byte 15 == 1) are touched.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static uint8_t ecc_f[256], ecc_b[256];
static uint32_t edc_lut[256];

static void init(void)
{
	for (uint32_t i = 0; i < 256; i++) {
		uint32_t j = (i << 1) ^ (i & 0x80 ? 0x11D : 0);
		ecc_f[i] = (uint8_t)j;
		ecc_b[i ^ j] = (uint8_t)i;
		uint32_t e = i;
		for (j = 0; j < 8; j++) e = (e >> 1) ^ (e & 1 ? 0xD8018001 : 0);
		edc_lut[i] = e;
	}
}

static uint32_t edc(const uint8_t *p, size_t n)
{
	uint32_t e = 0;
	while (n--) e = (e >> 8) ^ edc_lut[(e ^ *p++) & 0xFF];
	return e;
}

static void ecc_part(const uint8_t *src, uint32_t major_count, uint32_t minor_count,
                     uint32_t major_mult, uint32_t minor_inc, uint8_t *dest)
{
	uint32_t size = major_count * minor_count;
	for (uint32_t major = 0; major < major_count; major++) {
		uint32_t index = (major >> 1) * major_mult + (major & 1);
		uint8_t a = 0, b = 0;
		for (uint32_t minor = 0; minor < minor_count; minor++) {
			uint8_t t = src[index];
			index += minor_inc;
			if (index >= size) index -= size;
			a ^= t; b ^= t; a = ecc_f[a];
		}
		a = ecc_b[ecc_f[a] ^ b];
		dest[major] = a;
		dest[major + major_count] = a ^ b;
	}
}

static void fix_sector(uint8_t *s)
{
	uint32_t e = edc(s, 0x810);
	s[0x810] = e; s[0x811] = e >> 8; s[0x812] = e >> 16; s[0x813] = e >> 24;
	memset(s + 0x814, 0, 8);
	ecc_part(s + 0xC, 86, 24, 2, 86, s + 0x81C);   /* P */
	ecc_part(s + 0xC, 52, 43, 86, 88, s + 0x8C8);  /* Q */
}

int main(int argc, char **argv)
{
	int check = argc > 1 && !strcmp(argv[1], "--check");
	const char *path = argv[check ? 2 : 1];
	if (argc < 2 + check) { fprintf(stderr, "usage: cdecc [--check] <track.bin> [first count]\n"); return 2; }
	init();
	FILE *f = fopen(path, check ? "rb" : "r+b");
	if (!f) { perror(path); return 1; }
	fseek(f, 0, SEEK_END);
	long total = ftell(f) / 2352;
	long first = 0, count = total;
	if (!check && argc >= 4) { first = atol(argv[2]); count = atol(argv[3]); }
	if (first + count > total) count = total - first;
	uint8_t s[2352], o[2352];
	long changed = 0;
	for (long i = first; i < first + count; i++) {
		fseek(f, i * 2352L, SEEK_SET);
		if (fread(s, 1, 2352, f) != 2352) break;
		if (s[15] != 1) continue;
		memcpy(o, s, 2352);
		fix_sector(s);
		if (memcmp(o, s, 2352)) {
			changed++;
			if (check) { if (changed <= 5) printf("sector %ld differs\n", i); }
			else { fseek(f, i * 2352L, SEEK_SET); fwrite(s, 1, 2352, f); }
		}
	}
	fclose(f);
	printf("%s: %ld sectors %s\n", path, changed, check ? "would change" : "rewritten");
	return 0;
}
