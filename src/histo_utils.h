#ifndef HISTO_UTILS_H
#define HISTO_UTILS_H

#include <string>

int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim);
int compute_snow_fraction(const std::string & infname);

short compute_zs_ng(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim);
#endif //HISTO_UTILS_H

