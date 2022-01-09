function anArray = growing_array_ok_pragma()

anArray = [];
for idx=1:100
    anArray = [anArray; idx]; %#ok<AGROW>
end

end
