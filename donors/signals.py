# Signal removed intentionally.
# DonorProfile is created on demand via get_or_create() in donor views.
# Creating a DonorProfile for every user (including patients/hospitals)
# was causing logic bugs in the donor list filter.
