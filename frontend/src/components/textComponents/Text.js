import React from "react";
import styled from "styled-components";
import { simplifyCurrency } from "components/functions/currencyHelpers";

const SimplifiedCurrency = ({ value }) => (
  <span title={value.toLocaleString()}>{simplifyCurrency(value)}</span>
);

const AuxiliarText = styled.span`
  color: ${(props) => props.color || "var(--color-text-gray)"};
  font-weight: bold;
  font-size: var(--font-size-min);
`;

export { SimplifiedCurrency, AuxiliarText };
