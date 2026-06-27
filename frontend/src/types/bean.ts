export interface Bean {
  id: string;
  name: string;
  roaster_id: string;
  roaster: string;
  producer_id: string | null;
  producer: string | null;
  farm_id: string | null;
  farm: string | null;
  country_code: string | null;
  country: string | null;
  variety_id: string | null;
  variety: string | null;
  process_id: string | null;
  process: string | null;
  notes: string | null;
  created_at: string;
}

export type BeanFormValues = {
  name: string;
  roaster: string;
  roasterId: string | null;
  producer: string;
  producerId: string | null;
  farm: string;
  farmId: string | null;
  country: string;
  countryCode: string | null;
  variety: string;
  varietyId: string | null;
  process: string;
  processId: string | null;
  notes: string;
};

export const emptyBeanFormValues: BeanFormValues = {
  name: "",
  roaster: "",
  roasterId: null,
  producer: "",
  producerId: null,
  farm: "",
  farmId: null,
  country: "",
  countryCode: null,
  variety: "",
  varietyId: null,
  process: "",
  processId: null,
  notes: "",
};

export function valuesFromBean(bean: Bean): BeanFormValues {
  return {
    name: bean.name,
    roaster: bean.roaster,
    roasterId: bean.roaster_id,
    producer: bean.producer ?? "",
    producerId: bean.producer_id,
    farm: bean.farm ?? "",
    farmId: bean.farm_id,
    country: bean.country ?? "",
    countryCode: bean.country_code,
    variety: bean.variety ?? "",
    varietyId: bean.variety_id,
    process: bean.process ?? "",
    processId: bean.process_id,
    notes: bean.notes ?? "",
  };
}

export function beanPayload(values: BeanFormValues) {
  return {
    name: values.name,
    roaster_id: values.roasterId,
    producer_id: values.producerId,
    farm_id: values.farmId,
    country_code: values.countryCode,
    variety_id: values.varietyId,
    process_id: values.processId,
    notes: values.notes || null,
  };
}
