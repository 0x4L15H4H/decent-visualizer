data "oci_objectstorage_namespace" "current" {}

resource "oci_identity_policy" "tofu_object_storage" {
  compartment_id = var.oci_tenancy_ocid
  name           = "decent-visualizer-tofu-object-storage"
  description    = "Lets the OpenTofu WIF identity manage the dedicated backup bucket."
  statements = [
    "Allow group Default/decent-visualizer-tofu to manage object-family in tenancy",
  ]
}

resource "oci_objectstorage_bucket" "sqlite_backups" {
  depends_on     = [oci_identity_policy.tofu_object_storage]
  compartment_id = var.oci_tenancy_ocid
  namespace      = data.oci_objectstorage_namespace.current.namespace
  name           = "decent-visualizer-sqlite-backups"
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  versioning     = "Disabled"
}

resource "oci_objectstorage_object_lifecycle_policy" "sqlite_backups" {
  # OCI validates the Object Storage service principal's IAM grant while this
  # rule is created. Apply that grant first.
  depends_on = [oci_identity_policy.vm_sqlite_backup]
  bucket    = oci_objectstorage_bucket.sqlite_backups.name
  namespace = data.oci_objectstorage_namespace.current.namespace

  rules {
    action      = "DELETE"
    is_enabled  = true
    name        = "delete-daily-snapshots-after-30-days"
    target      = "objects"
    time_amount = 30
    time_unit   = "DAYS"
  }
}

resource "oci_identity_dynamic_group" "vm_sqlite_backup" {
  compartment_id = var.oci_tenancy_ocid
  name           = "decent-visualizer-sqlite-backup-vm"
  description    = "Only the Decent Visualizer OCI VM may upload SQLite backups."
  matching_rule  = "ALL {instance.id = '${var.external_vm_instance_ocid}'}"
}

resource "oci_identity_policy" "vm_sqlite_backup" {
  compartment_id = var.oci_tenancy_ocid
  name           = "decent-visualizer-sqlite-backup-vm"
  description    = "Lets the backup VM and OCI lifecycle service use only the private backup bucket."
  statements = [
    "Allow dynamic-group Default/${oci_identity_dynamic_group.vm_sqlite_backup.name} to read buckets in tenancy where target.bucket.name = '${oci_objectstorage_bucket.sqlite_backups.name}'",
    "Allow dynamic-group Default/${oci_identity_dynamic_group.vm_sqlite_backup.name} to manage objects in tenancy where target.bucket.name = '${oci_objectstorage_bucket.sqlite_backups.name}'",
    "Allow service objectstorage-${var.oci_region} to manage object-family in tenancy where target.bucket.name = '${oci_objectstorage_bucket.sqlite_backups.name}'",
  ]
}
