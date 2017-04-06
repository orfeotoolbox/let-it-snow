#include "histo_utils.h"

int main(int argc, char * argv[])
{
  if (argc != 10)
    {
      std::cout << "infname inmasksnowfname inmaskcloudfname dz fsnow_lim reverse offset center_offset histo_file" << std::endl;
    }

  return compute_snowline(argv[1], argv[2], argv[3], atoi(argv[4]), atof(argv[5]), atoi(argv[6]), atoi(argv[7]), atoi(argv[8]), argv[9]);
  
}
