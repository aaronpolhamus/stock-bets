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
  line-height: 1.2;
`;

const SectionTitle = styled.h2`
  font-size: var(--font-size-small);
  color: ${(props) => props.color || "var(--color-text-primary)"};
  text-transform: uppercase;
  font-weight: bold;
  letter-spacing: var(--letter-spacing-smallcaps);
`;

const TextButton = styled.button`
  font-size: ${(props) => props.size || "var(--font-size-min)"};
  color: ${(props) => props.color || "var(--text-primary)"};
  background-color: transparent;
  border: none;
  padding: 0;
`;

const FlexRow = styled.div`
  display: flex;
  width: 100%;
  justify-content: ${(props) => props.justify || "center"};
  align-items: ${(props) => props.align || "center"};
`;

export { SimplifiedCurrency, AuxiliarText, SectionTitle, TextButton, FlexRow };
