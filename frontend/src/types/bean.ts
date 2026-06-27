export interface EntityReference {
  id: string;
  name: string;
}

export interface CountryReference {
  code: string;
  name: string;
}

export interface Bean {
  id: string;
  name: string;
  roaster: EntityReference;
  producer: EntityReference | null;
  farm: EntityReference | null;
  country: CountryReference | null;
  variety: EntityReference | null;
  process: EntityReference | null;
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
    roaster: bean.roaster.name,
    roasterId: bean.roaster.id,
    producer: bean.producer?.name ?? "",
    producerId: bean.producer?.id ?? null,
    farm: bean.farm?.name ?? "",
    farmId: bean.farm?.id ?? null,
    country: bean.country?.name ?? "",
    countryCode: bean.country?.code ?? null,
    variety: bean.variety?.name ?? "",
    varietyId: bean.variety?.id ?? null,
    process: bean.process?.name ?? "",
    processId: bean.process?.id ?? null,
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
