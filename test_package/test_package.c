#include <netcdf.h>

#include <stdio.h>

int main() {
  printf("NetCDF version: %s\n", nc_inq_libvers());
  printf("*** SUCCESS!\n");
  return 0;
}
