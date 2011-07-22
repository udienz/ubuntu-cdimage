#ifndef MEMORY_H
#define MEMORY_H

#if 1

void *block_malloc(size_t size);
void block_free(void *vmem, size_t size);
void *block_realloc(void *vmem, size_t oldsize, size_t newsize);
char *block_strdup(char *from);

#else

#define block_malloc(x) malloc(x)
#define block_free(x, s) free(x)
#define block_realloc(x,z,y) realloc(x,y)
#define block_strdup(x) strdup(x)

static void print_memblock_summary(void) {}

#endif

#endif /* MEMORY_H */
