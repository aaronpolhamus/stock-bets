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

const SmallText = styled.span`
  color: ${(props) => props.color || "inherit"};
  font-size: var(--font-size-min);
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

const AlignText = styled.div`
  text-align: ${(props) => props.align || "left"};
`;

const FormFooter = styled.div`
  margin-top: var(--space-400);
  text-align: ${(props) => props.align || "right"};
`;

const Label = styled.p`
  font-size: var(--font-size-min);
  text-transform: uppercase;
  color: var(--color-text-gray);
  margin: 0 0 var(--space-50) 0;
  letter-spacing: var(--letter-spacing-smallcaps);
`;

const Subtext = styled.small`
  display: block;
  color: var(--color-text-gray);
`;

const SmallCaps = styled.small`
  font-size: var(--font-size-min);
  font-weight: 400;
  letter-spacing: var(--letter-spacing-smallcaps);
  text-transform: uppercase;
  color: ${(props) => props.color || "var(--color-text-primary)"};
`;

const CustomTr = styled.tr`
  white-space: nowrap;
  td {
    position: relative;
  }
`;

const OnHoverToggle = styled.div`
  opacity: 0;
  background-color: pink;
  position: absolute;
  top: 10px;
  transition: all 0.5s;
  tr:hover & {
    opacity: 1;
  }
`;

export {
  AlignText,
  AuxiliarText,
  CustomTr,
  FlexRow,
  FormFooter,
  Label,
  OnHoverToggle,
  SimplifiedCurrency,
  SectionTitle,
  SmallCaps,
  Subtext,
  TextButton,
  SmallText,
};
